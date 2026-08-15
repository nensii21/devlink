import io
import json
import logging

from app.core.config import settings
from app.schemas.user import ResumeParseResponse

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service to parse resumes (PDF/DOCX) and extract structured data using AI."""

    @staticmethod
    def _extract_text_from_pdf(file_bytes: bytes) -> str:
        try:
            import pypdf
        except ImportError:
            logger.error("pypdf is not installed.")
            return ""

        try:
            pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    @staticmethod
    def _extract_text_from_docx(file_bytes: bytes) -> str:
        try:
            import docx
        except ImportError:
            logger.error("python-docx is not installed.")
            return ""

        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""

    @staticmethod
    def parse_resume(file_bytes: bytes, filename: str) -> ResumeParseResponse:
        """Extract text from the resume file and parse it into a structured format."""

        # 1. Extract text
        text = ""
        if filename.lower().endswith(".pdf"):
            text = ResumeParserService._extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith(".docx"):
            text = ResumeParserService._extract_text_from_docx(file_bytes)

        if not text.strip():
            logger.warning("Could not extract any text from the resume.")
            return ResumeParseResponse()

        # 2. Use AI to parse the text
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, cannot parse resume.")
            return ResumeParseResponse()

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = (
                "You are an expert resume parser. Extract the following information from the provided resume text:\n"
                "1. skills: A list of general skills (e.g., 'Project Management', 'Agile', 'Team Leadership').\n"
                "2. technologies: A list of specific technologies, programming languages, and tools (e.g., 'Python', 'React', 'Docker').\n"
                "3. experience: A list of objects, each containing 'company', 'role', 'start_date', 'end_date', and 'description'.\n"
                "4. education: A list of objects, each containing 'institution', 'degree', 'field_of_study', 'start_date', 'end_date'.\n"
                "5. certifications: A list of objects, each containing 'name', 'issuer', 'date'.\n\n"
                "Return the result strictly as a valid JSON object with the exact keys: 'skills', 'technologies', 'experience', 'education', 'certifications'.\n"
                "Do not include any markdown formatting, code blocks, or extra text.\n\n"
                f"RESUME TEXT:\n{text[:15000]}"  # Limit text to avoid token limits
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output strictly JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            if result_text:
                parsed_data = json.loads(result_text)
                return ResumeParseResponse(
                    skills=parsed_data.get("skills", []),
                    technologies=parsed_data.get("technologies", []),
                    experience=parsed_data.get("experience", []),
                    education=parsed_data.get("education", []),
                    certifications=parsed_data.get("certifications", []),
                )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to parse resume with OpenAI: {e}")

        return ResumeParseResponse()
