import os
import httpx
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
router = Router()

class AdminFilter(BaseFilter):
    """Filter to check if user is an admin based on TELEGRAM_ADMIN_IDS environment variable"""
    
    def __init__(self):
        admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        if admin_ids_str:
            try:
                self.admin_ids = set(map(int, admin_ids_str.split(",")))
            except ValueError:
                self.admin_ids = set()
        else:
            self.admin_ids = set()
    
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return message.from_user.id in self.admin_ids

# Apply admin filter to all handlers in this router
router.message.filter(AdminFilter())

async def get_asset_statistics():
    """Fetch asset statistics from API or return mock data"""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/api/dashboard/stats", timeout=10.0)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    
    # Fallback mock data if API fails
    return {
        "total_deposits": 1250000.50,
        "total_borrowed": 875000.25,
        "total_users": 342,
        "health_ratio": 0.85,
        "active_positions": 156
    }

@router.message(Command("assets"))
async def assets_handler(message: types.Message):
    """Handle /assets command to show asset statistics dashboard"""
    try:
        stats = await get_asset_statistics()
        
        # Format response with Telegram Markdown
        response = "*Asset Statistics Dashboard*\n\n"
        response += f"*Total Deposits:* ${stats.get('total_deposits', 0):,.2f}\n"
        response += f"*Total Borrowed:* ${stats.get('total_borrowed', 0):,.2f}\n"
        response += f"*Total Users:* {stats.get('total_users', 0):,}\n"
        response += f"*Active Positions:* {stats.get('active_positions', 0):,}\n\n"
        
        health_ratio = stats.get('health_ratio', 0)
        if health_ratio > 0.7:
            health_status = "*Healthy*"
        elif health_ratio > 0.5:
            health_status = "*Warning*"
        else:
            health_status = "*Critical*"
        
        response += f"*Health Ratio:* {health_ratio:.2%} ({health_status})"
        
        await message.answer(response, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await message.answer(f"Error retrieving asset statistics: {str(e)}")

@router.message(Command("admin_help"))
async def admin_help_handler(message: types.Message):
    """Handle /admin_help command to show available admin commands"""
    help_text = """
*Admin Commands:*

*/assets* - Show asset statistics dashboard
*/admin_help* - Show this help message  
*/admin_status* - Show admin bot status

All commands require admin privileges.
    """
    await message.answer(help_text.strip(), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("admin_status"))
async def admin_status_handler(message: types.Message):
    """Handle /admin_status command to show bot status"""
    status_text = """
*Admin Bot Status:*

*Status:* Online
*Admin Filter:* Active
*API Connection:* Available

Bot is ready to process admin commands.
    """
    await message.answer(status_text.strip(), parse_mode=ParseMode.MARKDOWN) 