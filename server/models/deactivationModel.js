const { getDbConnection } = require('../config/database');

class DeactivationModel {
  /**
   * Sets account status to 'DEACTIVATED' and hides public profile visibility.
   */
  static async updateAccountStatus(userId, status) {
    const db = await getDbConnection();
    await db.beginTransaction();

    try {
      const allowedStatuses = ['ACTIVE', 'DEACTIVATED'];
      if (!allowedStatuses.includes(status)) {
        throw new Error('Invalid account status transition parameter.');
      }

      // 1. Update status flag and toggle public profile structural visibility
      const isPublic = status === 'ACTIVE' ? 1 : 0;
      await db.execute(
        'UPDATE users SET status = ?, is_public_profile = ? WHERE id = ?',
        [status, isPublic, userId]
      );

      // 2. Safe Project Ownership Handling: Ensure projects remain visible to contributors
      // We explicitly preserve project ownership so data isn't dropped, but optionally flag
      // the status of projects matching a deactivated user to prevent public listing
      await db.execute(
        'UPDATE projects SET visibility_status = ? WHERE owner_id = ? AND is_shared = false',
        [status === 'ACTIVE' ? 'PUBLIC' : 'HIDDEN', userId]
      );

      await db.commit();
      return true;
    } catch (error) {
      await db.rollback();
      console.error(`Status change transaction failed for user ID ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Resolves a user profile matching email parameters to verify current state metrics.
   */
  static async findUserByEmail(email) {
    const db = await getDbConnection();
    const [rows] = await db.execute(
      'SELECT id, email, password_hash, status FROM users WHERE email = ?',
      [email]
    );
    return rows[0] || null;
  }
}

module.exports = DeactivationModel;
