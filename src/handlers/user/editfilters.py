import json
from pathlib import Path
from urllib.parse import urlparse

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery

from src.core.bot import SettingsBot
from src.keyboards.callbackdata import *
from src.keyboards.inline import Ikb as IKB

from request import *
from manager import thread_manager


class EditFilterCar(StatesGroup):
    MIN_PRICE = State()
    MAX_PRICE = State()


class EditFiltersHandlers:
    def __init__(self, module: SettingsBot) -> None:
        self.bot = module.bot
        self.dp = module.dp
        self.cfg = module.config


    async def register_handlers(self):
        self.dp.callback_query(FiltersCallback.filter(F.action == 'edit_filter'))(self.edit_filter)
        self.dp.callback_query(FiltersCallback.filter(F.action == 'back_edit_menu'))(self.back_filter_menu)

        self.dp.callback_query(F.data == 'edit_model')(self.edit_model)
        self.dp.callback_query(ModelsCallback.filter(F.action == 'edit_model'))(self.get_new_model)

        self.dp.callback_query(F.data == 'edit_typengines')(self.edit_typegines)
        self.dp.callback_query(TypengineCallback.filter(F.action == 'edit_typengine'))(self.get_new_typengines)

        self.dp.callback_query(F.data == 'edit_min_year')(self.edit_min_year)
        self.dp.callback_query(YearsCallback.filter(F.action == 'edit_min_year'))(self.edit_min_years)
        self.dp.callback_query(F.data == 'edit_max_year')(self.edit_max_year)
        self.dp.callback_query(YearsCallback.filter(F.action == 'edit_max_year'))(self.edit_max_years)

        self.dp.callback_query(F.data == 'edit_min_displacement')(self.edit_min_displacement)
        self.dp.callback_query(DisplacementCallback.filter(F.action == 'edit_min_displacement'))(self.edit_min_displacements)
        self.dp.callback_query(F.data == 'edit_max_displacement')(self.edit_max_displacement)
        self.dp.callback_query(DisplacementCallback.filter(F.action == 'edit_max_displacement'))(self.edit_max_displacements)

        self.dp.callback_query(F.data == 'edit_gearbox')(self.edit_gearbox)
        self.dp.callback_query(GearboxCallback.filter(F.action == 'edit_gearbox'))(self.get_new_gearbox)

        self.dp.callback_query(F.data == 'edit_bodytypes')(self.edit_bodytypes)
        self.dp.callback_query(BodytypeCallback.filter(F.action == 'edit_bodytype'))(self.get_new_bodytypes)

        self.dp.callback_query(F.data == 'edit_min_price')(self.edit_min_price)
        self.dp.message(StateFilter(F.text.isdigit(), EditFilterCar.MIN_PRICE))(self.get_new_min_price)
        self.dp.callback_query(F.data == 'edit_max_price')(self.edit_max_price)
        self.dp.message(StateFilter(F.text.isdigit(), EditFilterCar.MAX_PRICE))(self.get_new_max_price)

    
    def _load_db(self, path: str = "data_tasks/cars.json") -> dict:
        try:
            with open(Path(path), "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}

    
    def update_json_cars(self, filter_id: str, new_data: dict, uid: int, path: str = "data_tasks/cars.json") -> dict:
        db = self._load_db()
        record = db.get(filter_id, {})

        for k, v in new_data.items():
            if v in (None, "", 0):
                record.pop(k, None)
            else:
                record[k] = v

        db[filter_id] = record

        with open(Path(path), "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)

        return db


    def update_json_threads(self, filter_id: str, new_data: dict, uid: int, path: str = "data_tasks/active_threads.json"):
        db = self._load_db(path=path)

        user_filters = db.get(str(uid), [])
        for item in user_filters:
            if filter_id in item:
                record = item[filter_id]

                for k, v in new_data.items():
                    if v in (None, "", 0):
                        record.pop(k, None)
                    else:
                        record[k] = v

                item[filter_id] = record
                break

        db[str(uid)] = user_filters

        with open(Path(path), "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)


    async def edit_filter(self, call: CallbackQuery, callback_data: FiltersCallback, state: FSMContext) -> Message:
        db = self._load_db()

        filter_data = db.get(callback_data.filter_id)
        await state.update_data(filter_data=filter_data, filter_id=callback_data.filter_id)
        
        return await call.message.edit_text(f'You selected: {filter_data.get("name_car")}. Select what you want to change.', reply_markup=await IKB.edit_filter_menu(
            filter_id=callback_data.filter_id, filters_data=filter_data
        ))

    
    async def back_filter_menu(self, call: CallbackQuery, callback_data: FiltersCallback, state: FSMContext) -> Message:
        return await self.edit_filter(call=call, callback_data=callback_data, state=state)


    async def edit_model(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        name_car = filter_data.get('name_car')
        current_model = filter_data.get('model') or '<i>Not selected</i>'

        if name_car == "BMW":
            series = [
                "1 series", "2 series", "3 series", "4 series", "5 series", "6 series",
                "7 series", "8 series", "M series", "X series", "Z series", "i series"
            ]
            models = [serie for serie in series]
            await state.update_data(models=models)

            text = (
                f"🚘 <b>Brand:</b> {name_car}\n"
                f"📍 <b>Current model:</b> {current_model}\n\n"
                f"➡️ <u>Please select a new model</u>:"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_edit_menu(
                    models=models,
                    filter_id=data.get('filter_id'),
                    current_model=current_model
                )
            )
        
        elif name_car == "Mercedes":
            classes = [
                "A-class", "B-Class", "C-class", "CL-class", "CLA-class", "CLK-class", "CLS-class",
                "E-class", "G-class", "GL-clase", "GLA-class", "GLB-class", "GLC-class", "GLE-class",
                "GLK-clase", "GLS-class", "ML-class", "R-class", "S-class", "SL-class", "SLK-class",
                "V-class", "X-class", "Mercedes-benz", "Citan", "Sprinter", "Vaneo", "Viano", "Vito"
            ]
            models = [class_id for class_id in classes]
            await state.update_data(models=models)

            text = (
                f"🚘 <b>Brand:</b> {name_car}\n"
                f"📍 <b>Current model:</b> {current_model}\n\n"
                f"➡️ <u>Please select a new model</u>:"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_edit_menu(
                    models=models,
                    filter_id=data.get('filter_id'),
                    current_model=current_model
                )
            )
        
        else:
            models_cars = await get_models_cars(url=filter_data.get('url') + 'search/')
            if not models_cars:
                return await call.message.edit_text("❌ <b>No models available</b>")

            await state.update_data(models=models_cars)

            text = (
                f"🚘 <b>Brand:</b> {name_car}\n"
                f"📍 <b>Current model:</b> {current_model}\n\n"
                f"➡️ <u>Please select a new model</u>:"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_edit_menu(
                    models=models_cars, filter_id=data.get('filter_id'), current_model=current_model
                )
            )


    async def get_new_model(self, call: CallbackQuery, callback_data: ModelsCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        models = data.get('models', [])
        filter_id = data.get('filter_id')
        filter_data = data.get('filter_data', {})
        car = filter_data.get('name_car')
        model = filter_data.get('model', None)

        selected_models = None
        if car in ("BMW", "Mercedes") and callback_data.model:
            models_search = await get_models(url=filter_data.get('url'))
            if models_search:
                selected = models_search.get(callback_data.model)
                if selected:
                    selected_models = selected
                else:
                    selected_models = callback_data.model if callback_data.model != model else None

        if callback_data.model == model:
            return

        new_data = {"models": selected_models or callback_data.model, "model": callback_data.model}

        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["models"] = selected_models or callback_data.model
        filter_data["model"] = callback_data.model
        await state.update_data(filter_data=filter_data)

        text = (
            f"🚘 <b>Brand:</b> {filter_data.get('name_car', '<i>Not selected</i>')}\n"
            f"📍 <b>Current model:</b> {callback_data.model or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Please select a new model</u>:"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_edit_menu(
                models=models,
                filter_id=filter_id,
                current_model=callback_data.model or "<i>Not selected</i>"
            )
        )


    async def edit_typegines(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)

        typengines = await get_typengines(url=filter_data.get('url') + 'search/')
        if not typengines:
            return await call.message.edit_text("❌ <b>No engine types available</b>", parse_mode="HTML")

        await state.update_data(typengines=typengines)

        text = (
            f"⚙️ <b>Engine types for {filter_data.get('name_car')}</b>\n"
            f"(you can select multiple)\n\n"
            f"📍 <b>Selected:</b> {', '.join(filter_data.get('typengines', [])) or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.typengine_buttons_edit_menu(
                typengines=typengines,
                filter_id=data.get('filter_id'),
                selected_typengines=filter_data.get('typengines') or []
            )
        )

    
    async def get_new_typengines(self, call: CallbackQuery, callback_data: TypengineCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        typengines = data.get('typengines', [])
        filter_id = data.get('filter_id')
        filter_typengines = filter_data.get('typengines') or []

        if callback_data.typengine not in filter_typengines:
            filter_typengines.append(callback_data.typengine)
        else:
            filter_typengines.remove(callback_data.typengine)

        new_data = {"typengines": filter_typengines}

        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["typengines"] = filter_typengines
        await state.update_data(filter_data=filter_data)

        text = (
            f"⚙️ <b>Engine types for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n"
            f"(you can select multiple)\n\n"
            f"📍 <b>Selected:</b> {', '.join(filter_typengines) or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.typengine_buttons_edit_menu(
                typengines=typengines,
                filter_id=data.get('filter_id'),
                selected_typengines=filter_typengines or []
            )
        )

    
    async def edit_min_year(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        years = await get_years(url=filter_data.get('url') + 'search/')
        if not years:
            return await call.message.edit_text("❌ <b>No years available</b>", parse_mode="HTML")

        await state.update_data(years=years)

        text = (
            f"📅 <b>Select minimum year for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {filter_data.get('min_year') or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_edit_menu(
                years=years,
                filter_id=data.get('filter_id'),
                current_value=filter_data.get('min_year') or "<i>Not selected</i>",
                action='edit_min_year'
            )
        )

    
    async def edit_min_years(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        years = data.get('years', [])
        filter_id = data.get('filter_id')
        min_year = filter_data.get('min_year', None)

        if callback_data.year == min_year:
            return
        
        new_data = {"min_year": callback_data.year}

        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["min_year"] = callback_data.year
        await state.update_data(filter_data=filter_data)

        text = (
            f"📅 <b>Select minimum year for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {callback_data.year or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_edit_menu(
                years=years,
                filter_id=data.get('filter_id'),
                current_value=callback_data.year or "<i>Not selected</i>",
                action='edit_min_year'
            )
        )


    async def edit_max_year(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        years = await get_years(url=filter_data.get('url') + 'search/')
        if not years:
            return await call.message.edit_text("❌ <b>No years available</b>", parse_mode="HTML")

        await state.update_data(years=years)

        text = (
            f"📅 <b>Select maximum year for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {filter_data.get('max_year') or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_edit_menu(
                years=years,
                filter_id=data.get('filter_id'),
                current_value=filter_data.get('max_year') or "<i>Not selected</i>",
                action='edit_max_year'
            )
        )

    
    async def edit_max_years(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        years = data.get('years', [])
        filter_id = data.get('filter_id')
        max_year = filter_data.get('max_year', None)

        if callback_data.year == max_year:
            return

        new_data = {"max_year": callback_data.year}
        
        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["max_year"] = callback_data.year
        await state.update_data(filter_data=filter_data)

        text = (
            f"📅 <b>Select maximum year for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {callback_data.year or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_edit_menu(
                years=years,
                filter_id=data.get('filter_id'),
                current_value=callback_data.year or "<i>Not selected</i>",
                action='edit_max_year'
            )
        )

    
    async def edit_min_displacement(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        displacements = await get_displacement_motor(url=filter_data.get('url'))
        if not displacements:
            return await call.message.edit_text("❌ <b>No displacement values available</b>", parse_mode="HTML")

        await state.update_data(displacements=displacements)

        text = (
            f"⚙️ <b>Select minimum displacement for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {filter_data.get('min_displacement') or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements,
                filter_id=data.get('filter_id'),
                current_value=filter_data.get('min_displacement') or "<i>Not selected</i>",
                action='edit_min_displacement'
            )
        )

    
    async def edit_min_displacements(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        displacements = data.get('displacements', [])
        filter_id = data.get('filter_id')
        min_displacement = filter_data.get('min_displacement', None)

        if callback_data.displacement == min_displacement:
            return

        new_data = {"min_displacement": callback_data.displacement}
        
        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["min_displacement"] = callback_data.displacement
        await state.update_data(filter_data=filter_data)

        text = (
            f"⚙️ <b>Select minimum displacement for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {callback_data.displacement or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(
            text,
            reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements,
                filter_id=data.get('filter_id'),
                current_value=callback_data.displacement or "<i>Not selected</i>",
                action='edit_min_displacement'
            )
        )

    
    async def edit_max_displacement(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        displacements = await get_displacement_motor(url=filter_data.get('url'))
        if not displacements:
            return await call.message.edit_text("❌ <b>No displacement values available</b>", parse_mode="HTML")

        await state.update_data(displacements=displacements)

        text = (
            f"⚙️ <b>Select maximum displacement for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {filter_data.get('max_displacement') or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements,
                filter_id=data.get('filter_id'),
                current_value=filter_data.get('max_displacement') or "<i>Not selected</i>",
                action='edit_max_displacement'
            )
        )


    
    async def edit_max_displacements(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        displacements = data.get('displacements', [])
        filter_id = data.get('filter_id')
        max_displacement = filter_data.get('max_displacement', None)

        if callback_data.displacement == max_displacement:
            return

        new_data = {"max_displacement": callback_data.displacement}
        
        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["max_displacement"] = callback_data.displacement
        await state.update_data(filter_data=filter_data)

        text = (
            f"⚙️ <b>Select maximum displacement for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {callback_data.displacement or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements,
                filter_id=data.get('filter_id'),
                current_value=callback_data.displacement or "<i>Not selected</i>",
                action='edit_max_displacement'
            )
        )

    
    async def edit_gearbox(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        gearbox = await get_gearbox(url=filter_data.get('url') + 'search/')
        if not gearbox:
            return await call.message.edit_text("❌ <b>No gearbox options available</b>", parse_mode="HTML")

        await state.update_data(gearbox=gearbox)

        text = (
            f"⚙️ <b>Select gearbox for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {filter_data.get('gearbox') or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.gerabox_buttons_edit_menu(
                geraboxes=gearbox,
                filter_id=data.get('filter_id'),
                current_value=filter_data.get('gearbox') or "<i>Not selected</i>"
            )
        )

    
    async def get_new_gearbox(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        gearboxes = data.get('gearbox', [])
        filter_id = data.get('filter_id')
        gearbox = filter_data.get('gearbox', None)

        if callback_data.gearbox == gearbox:
            return

        new_data = {"gearbox": callback_data.gearbox}
        
        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["gearbox"] = callback_data.gearbox
        await state.update_data(filter_data=filter_data)

        text = (
            f"⚙️ <b>Select gearbox for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n\n"
            f"📍 <b>Selected:</b> {callback_data.gearbox or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.gerabox_buttons_edit_menu(
                geraboxes=gearboxes,
                filter_id=data.get('filter_id'),
                current_value=callback_data.gearbox or "<i>Not selected</i>"
            )
        )

    
    async def edit_bodytypes(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)

        bodytypes = await get_bodytype(url=filter_data.get('url') + 'search/')
        if not bodytypes:
            return await call.message.edit_text("❌ <b>No body types available</b>", parse_mode="HTML")

        await state.update_data(bodytypes=bodytypes)

        text = (
            f"🚘 <b>Select body types for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n"
            f"(you can select multiple)\n\n"
            f"📍 <b>Selected:</b> {', '.join(filter_data.get('bodytypes', [])) or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.bodytype_buttons_edit_menu(
                bodytypes=bodytypes,
                filter_id=data.get('filter_id'),
                selected_bodytypes=filter_data.get('bodytypes') or []
            )
        )


    async def get_new_bodytypes(self, call: CallbackQuery, callback_data: BodytypeCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        bodytypes = data.get('bodytypes', [])
        filter_id = data.get('filter_id')
        filter_bodytypes = filter_data.get('bodytypes') or []

        if callback_data.bodytype not in filter_bodytypes:
            filter_bodytypes.append(callback_data.bodytype)
        else:
            filter_bodytypes.remove(callback_data.bodytype)

        new_data = {"bodytypes": filter_bodytypes}

        self.update_json_cars(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=call.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=call.from_user.id, new_filter={filter_id: new_data})

        filter_data["bodytypes"] = filter_bodytypes
        await state.update_data(filter_data=filter_data)

        text = (
            f"🚘 <b>Select body types for {filter_data.get('name_car', '<i>Not selected</i>')}</b>\n"
            f"(you can select multiple)\n\n"
            f"📍 <b>Selected:</b> {', '.join(filter_bodytypes) or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.bodytype_buttons_edit_menu(
                bodytypes=bodytypes,
                filter_id=filter_id,
                selected_bodytypes=filter_bodytypes or []
            )
        )

    
    async def edit_min_price(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.set_state(EditFilterCar.MIN_PRICE)

        text = (
            "💰 <b>Please enter the minimum price</b>\n\n"
            "➡️ Send <b>0</b> to skip setting a minimum price."
        )

        return await call.message.edit_text(text)


    async def get_new_min_price(self, m: Message, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        filter_id = data.get('filter_id')

        new_data = {"min_price": int(m.text)}

        self.update_json_cars(
            new_data=new_data,
            uid=m.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=m.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=m.from_user.id, new_filter={filter_id: new_data})

        filter_data["min_price"] = int(m.text)
        await state.update_data(filter_data=filter_data)

        await m.answer("✅ <b>Minimum price successfully updated!</b>")

        text = (
            f"🚗 <b>You selected:</b> {filter_data.get('name_car', '<i>Not selected</i>')}\n\n"
            f"⚙️ <b>Select what you want to change:</b>"
        )

        return await m.answer(text, reply_markup=await IKB.edit_filter_menu(
                filter_id=filter_id,
                filters_data=filter_data
            )
        )

    
    async def edit_max_price(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.set_state(EditFilterCar.MAX_PRICE)

        text = (
            "💰 <b>Please enter the maximum price</b>\n\n"
            "➡️ Send <b>0</b> to skip setting a maximum price."
        )

        return await call.message.edit_text(text)


    async def get_new_max_price(self, m: Message, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        filter_id = data.get('filter_id')

        new_data = {"max_price": int(m.text)}

        self.update_json_cars(
            new_data=new_data,
            uid=m.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data=new_data,
            uid=m.from_user.id,
            filter_id=filter_id
        )

        thread_manager.update_filter(uid=m.from_user.id, new_filter={filter_id: new_data})

        filter_data["max_price"] = int(m.text)
        await state.update_data(filter_data=filter_data)

        await m.answer("✅ <b>Maximum price successfully updated!</b>", parse_mode="HTML")

        text = (
            f"🚗 <b>You selected:</b> {filter_data.get('name_car', '<i>Not selected</i>')}\n\n"
            f"⚙️ <b>Select what you want to change:</b>"
        )

        return await m.answer(text, reply_markup=await IKB.edit_filter_menu(
                filter_id=filter_id,
                filters_data=filter_data
            )
        )
