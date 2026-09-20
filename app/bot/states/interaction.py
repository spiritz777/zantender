"""States used by the Telegram MVP interaction flows."""

from aiogram.fsm.state import State, StatesGroup


class DocumentAnalysisState(StatesGroup):
    waiting_for_document = State()


class CompanyProfileState(StatesGroup):
    waiting_for_description = State()


class ConsultantState(StatesGroup):
    waiting_for_question = State()
