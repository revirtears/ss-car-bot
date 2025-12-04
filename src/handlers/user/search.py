import json
from pathlib import Path

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.core.bot import SettingsBot
from src.keyboards.callbackdata import *
from src.keyboards.inline import Ikb as IKB

from manager import thread_manager


class SearchHandlers:
    def __init__(self, module: SettingsBot) -> None:
        self.bot = module.bot
        self.dp = module.dp
        self.cfg = module.config


    async def register_handlers(self):
        self.dp.message(Command("search"))(self.command_search_start)
        self.dp.message(Command("stop"))(self.command_search_stop)

        self.dp.callback_query(F.data == 'filters')(self.get_filters)
        self.dp.callback_query(FiltersCallback.filter(F.action == 'filter'))(self.get_filter)
        self.dp.callback_query(FiltersCallback.filter(F.action == 'delete_filter'))(self.delete_filter)

        self.dp.callback_query(F.data == 'back_main_menu')(self.back_main_menu)
        self.dp.callback_query(F.data == 'back_filters')(self.back_filters)
        self.dp.callback_query(FiltersCallback.filter(F.action == 'back_filter'))(self.back_filter)

        self.dp.callback_query(FiltersCallback.filter(F.action == 'on_filter'))(self.filter_turn_on)
        self.dp.callback_query(FiltersCallback.filter(F.action == 'off_filter'))(self.filter_turn_off)

    
    def _load_db(self) -> dict:
        try:
            with open(Path('data_tasks/cars.json'), "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}


    async def command_search_start(self, m: Message) -> Message:
        db = self._load_db()

        filtered = {k: v for k, v in db.items() if v.get("uid") == m.from_user.id}
        if not filtered:
            return await m.answer("<b>Not found filters!</b>")

        thread_manager.start_threads(data_search=filtered, uid=m.from_user.id)

        return await m.answer(f"<b>{len(filtered)} filters found, search started successfully!</b>")

    
    async def command_search_stop(self, m: Message) -> Message:
        thread_manager.stop_threads(uid=m.from_user.id)

        return await m.answer(f"<b>All filters have been stopped successfully!</b>")

    
    async def get_filters(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.clear()
        db = self._load_db()

        filtered_cars = [(k, v.get("name_car"), v.get("model")) for k, v in db.items() if v.get("uid") == call.from_user.id]
        if not filtered_cars:
            return await call.answer("You don't have filters!")

        return await call.message.edit_text(f"You have {len(filtered_cars)} filters.", reply_markup=await IKB.filters_menu(filters=filtered_cars, uid=call.from_user.id))

    
    async def get_filter(self, call: CallbackQuery, callback_data: FiltersCallback) -> Message:
        db = self._load_db()
        filter_id = callback_data.filter_id
        data = db.get(filter_id)

        selectors = {
            "name_car": "🚙 <b>{}</b>",
            "model": "📌 Model: <b>{}</b>",
            "min_year": "📅 Min. year: <b>{}</b>",
            "max_year": "📅 Max. year: <b>{}</b>",
            "min_price": "💰 Min. price: <b>{}</b>",
            "max_price": "💰 Max. price: <b>{}</b>",
            "min_displacement": "⚙️ Min. displacement: <b>{}</b>",
            "max_displacement": "⚙️ Max. displacement: <b>{}</b>",
            "typengines": "⛽ Engine types: <b>{}</b>",
            "gearbox": "🔧 Gearbox: <b>{}</b>",
            "bodytypes": "🚗 Bodytypes: <b>{}</b>",
            "checkup": "🩺 Checkup: <b>{}</b>",
        }

        parts = []
        for key, template in selectors.items():
            value = data.get(key)
            if value:
                if isinstance(value, list):
                    parts.append(template.format(", ".join(value)))
                else:
                    parts.append(template.format(value))
            else:
                parts.append(template.format("No selected"))

        message = (
            f"✨ <b>Filter details</b> ✨\n\n"
            + "\n".join(parts)
        )

        return await call.message.edit_text(
            message,
            reply_markup=await IKB.filter_menu(filter_id=filter_id, uid=call.from_user.id)
        )

    
    async def back_filter(self, call: CallbackQuery, callback_data: FiltersCallback, state: FSMContext) -> Message:
        await state.clear()
        return await self.get_filter(call=call, callback_data=callback_data)


    async def delete_filter(self, call: CallbackQuery, callback_data: FiltersCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        if not data.get('accept_delete_filter'):
            await state.update_data(accept_delete_filter=True)
            return await call.answer("Are you sure you want to remove this filter?", show_alert=True)

        filter_id = callback_data.filter_id 
        uid = call.from_user.id    

        try:
            with open(Path('data_tasks/active_threads.json'), "r", encoding="utf-8") as f:
                db1 = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): db1 = {}

        if str(uid) in db1:
            db1[str(uid)] = [entry for entry in db1[str(uid)] if filter_id not in entry]
            with open(Path('data_tasks/active_threads.json'), "w", encoding="utf-8") as f:
                json.dump(db1, f, ensure_ascii=False, indent=4)

        try:
            with open(Path('data_tasks/cars.json'), "r", encoding="utf-8") as f:
                db2 = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): db2 = {}

        if filter_id in db2:
            del db2[filter_id]
            with open(Path('data_tasks/cars.json'), "w", encoding="utf-8") as f:
                json.dump(db2, f, ensure_ascii=False, indent=4)

        thread_manager.remove_filter(uid=uid, key=filter_id)
        await state.clear()

        return await call.message.edit_text(f"<b>The filter has been successfully removed.</b>", reply_markup=await IKB.main_menu())

    
    async def back_main_menu(self, call: CallbackQuery) -> Message:
        return await call.message.edit_text("Hello! 👋\n\nWelcome to the bot for finding ads!", reply_markup=await IKB.main_menu())

    
    async def back_filters(self, call: CallbackQuery, state: FSMContext) -> Message:
        return await self.get_filters(call=call, state=state)

    
    async def filter_turn_on(self, call: CallbackQuery, callback_data: FiltersCallback) -> Message:
        db = self._load_db()

        thread_manager.start_threads(data_search={callback_data.filter_id: db[callback_data.filter_id]}, uid=call.from_user.id)

        return await call.message.edit_reply_markup(reply_markup=await IKB.filter_menu(filter_id=callback_data.filter_id, uid=call.from_user.id))
    

    async def filter_turn_off(self, call: CallbackQuery, callback_data: FiltersCallback) -> Message:
        thread_manager.remove_filter(key=callback_data.filter_id, uid=call.from_user.id)

        return await call.message.edit_reply_markup(reply_markup=await IKB.filter_menu(filter_id=callback_data.filter_id, uid=call.from_user.id))