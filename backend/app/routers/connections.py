from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.connection import Connection, ConnectionStatus
from app.models.user import User
from app.schemas.connection import (
    ConnectionActionResponse,
    ConnectionRequest,
    ConnectionResponse,
    ConnectionStatusResponse,
    MutualConnectionsResponse,
)

router = APIRouter(tags=["connections"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[Session, Depends(get_db)]


def _get_connection(db: Session, user_a: uuid.UUID, user_b: uuid.UUID):
    return db.execute(
        select(Connection).where(
            or_(
                and_(
                    Connection.requester_id == user_a, Connection.recipient_id == user_b
                ),
                and_(
                    Connection.requester_id == user_b, Connection.recipient_id == user_a
                ),
            )
        )
    ).scalar_one_or_none()


@router.post(
    "/request", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED
)
def send_connection_request(body: ConnectionRequest, current_user: CurrentUser, db: DB):
    if body.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself.")
    recipient = db.get(User, body.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found.")
    existing = _get_connection(db, current_user.id, body.recipient_id)
    if existing:
        if existing.status == ConnectionStatus.ACCEPTED:
            raise HTTPException(status_code=409, detail="Already connected.")
        if existing.status == ConnectionStatus.PENDING:
            raise HTTPException(status_code=409, detail="Request already pending.")
        if existing.status in (ConnectionStatus.DECLINED, ConnectionStatus.WITHDRAWN):
            existing.requester_id = current_user.id
            existing.recipient_id = body.recipient_id
            existing.status = ConnectionStatus.PENDING
            db.commit()
            db.refresh(existing)
            return existing
    conn = Connection(requester_id=current_user.id, recipient_id=body.recipient_id)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.post("/{connection_id}/respond", response_model=ConnectionActionResponse)
def respond_to_connection(
    connection_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    action: str = Query(..., pattern="^(accept|decline)$"),
):
    conn = db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection request not found.")
    if conn.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request to respond to.")
    if conn.status != ConnectionStatus.PENDING:
        raise HTTPException(
            status_code=409, detail=f"Cannot respond to a '{conn.status}' request."
        )
    conn.status = (
        ConnectionStatus.ACCEPTED if action == "accept" else ConnectionStatus.DECLINED
    )
    db.commit()
    db.refresh(conn)
    return {**conn.__dict__, "message": f"Connection {conn.status}."}


@router.post("/{connection_id}/withdraw", response_model=ConnectionActionResponse)
def withdraw_connection(connection_id: uuid.UUID, current_user: CurrentUser, db: DB):
    conn = db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection request not found.")
    if conn.requester_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only withdraw your own requests."
        )
    if conn.status != ConnectionStatus.PENDING:
        raise HTTPException(
            status_code=409, detail=f"Cannot withdraw a '{conn.status}' request."
        )
    conn.status = ConnectionStatus.WITHDRAWN
    db.commit()
    db.refresh(conn)
    return {**conn.__dict__, "message": "Connection request withdrawn."}


@router.get("/status/{user_id}", response_model=ConnectionStatusResponse)
def get_connection_status(user_id: uuid.UUID, current_user: CurrentUser, db: DB):
    conn = _get_connection(db, current_user.id, user_id)
    if not conn:
        return ConnectionStatusResponse(
            status=None, connection_id=None, is_connected=False, sent_by_me=False
        )
    return ConnectionStatusResponse(
        status=conn.status,
        connection_id=conn.id,
        is_connected=conn.status == ConnectionStatus.ACCEPTED,
        sent_by_me=conn.requester_id == current_user.id,
    )


@router.get("", response_model=list[ConnectionResponse])
def list_connections(
    current_user: CurrentUser,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return (
        db.execute(
            select(Connection)
            .where(
                and_(
                    or_(
                        Connection.requester_id == current_user.id,
                        Connection.recipient_id == current_user.id,
                    ),
                    Connection.status == ConnectionStatus.ACCEPTED,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )


@router.get("/pending/received", response_model=list[ConnectionResponse])
def list_received_pending(current_user: CurrentUser, db: DB):
    return (
        db.execute(
            select(Connection).where(
                and_(
                    Connection.recipient_id == current_user.id,
                    Connection.status == ConnectionStatus.PENDING,
                )
            )
        )
        .scalars()
        .all()
    )


@router.get("/pending/sent", response_model=list[ConnectionResponse])
def list_sent_pending(current_user: CurrentUser, db: DB):
    return (
        db.execute(
            select(Connection).where(
                and_(
                    Connection.requester_id == current_user.id,
                    Connection.status == ConnectionStatus.PENDING,
                )
            )
        )
        .scalars()
        .all()
    )


@router.get("/mutual/{user_id}", response_model=MutualConnectionsResponse)
def get_mutual_connections(user_id: uuid.UUID, current_user: CurrentUser, db: DB):
    def _accepted_ids(uid: uuid.UUID) -> set[uuid.UUID]:
        conns = (
            db.execute(
                select(Connection).where(
                    and_(
                        or_(
                            Connection.requester_id == uid,
                            Connection.recipient_id == uid,
                        ),
                        Connection.status == ConnectionStatus.ACCEPTED,
                    )
                )
            )
            .scalars()
            .all()
        )
        return {
            c.recipient_id if c.requester_id == uid else c.requester_id for c in conns
        }

    mutual = _accepted_ids(current_user.id) & _accepted_ids(user_id)
    return MutualConnectionsResponse(
        mutual_count=len(mutual), mutual_users=list(mutual)
    )
