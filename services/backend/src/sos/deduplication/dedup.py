from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import SOSReport


async def is_duplicate_msg(db: AsyncSession, msg_id: str) -> bool:
    """
    Checks if msg_id already exists in the SOSReport table.
    """
    stmt = select(SOSReport.sos_id).where(SOSReport.msg_id == msg_id).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
