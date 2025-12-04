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
        current_model = filter_data.get('model') or 'No selected'

        if name_car == "BMW":
            series = [
                "1 series", '2 series', '3 series', '4 series', '5 series', '6 series', '7 series', '8 series', 'M series', 'X series', 'Z series', 'i series'
            ]
            models = [serie for serie in series]
            await state.update_data(models=models)

            return await call.message.edit_text(
                f"Select a new model for {name_car}\nModel now: {current_model}", reply_markup=await IKB.models_buttons_edit_menu(
                    models=models, filter_id=data.get('filter_id'), current_model=current_model)
            )
        
        elif name_car == 'Mercedes':
            classes = [
                "A-class", "B-Class", "C-class", "CL-class", "CLA-class", "CLK-class", "CLS-class", "E-class", "G-class", "GL-clase", "GLA-class", "GLB-class", "GLC-class", "GLE-class", "GLK-clase", "GLS-class", "ML-class", "R-class", "S-class", "SL-class", "SLK-class", "V-class", "X-class", "Mercedes-benz"
            ]
            models = [class_id for class_id in classes]
            await state.update_data(models=models)

            return await call.message.edit_text(
                f"Select a new model for {name_car}\nModel now: {current_model}", reply_markup=await IKB.models_buttons_edit_menu(
                    models=models, filter_id=data.get('filter_id'), current_model=current_model)
            )
        
        else:
            models_cars = await get_models_cars(url=filter_data.get('url') + 'search/')
            if not models_cars:
                return await call.message.edit_text("No models") 

            await state.update_data(models=models_cars)

            return await call.message.edit_text(
                f"Select a new model for {name_car}\nModel now: {current_model}", reply_markup=await IKB.models_buttons_edit_menu(
                    models=models_cars, filter_id=data.get('filter_id'), current_model=current_model)
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
                selected_models = selected

        if callback_data.model == model:
            return

        self.update_json_cars(
            new_data={"models": selected_models or callback_data.model, 'model': callback_data.model},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"models": selected_models or callback_data.model, 'model': callback_data.model},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["models"] = selected_models or callback_data.model
        filter_data['model'] = callback_data.model
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select a new model for {filter_data.get('name_car')}\n"
            f"Model now: {callback_data.model or 'No selected'}",
            reply_markup=await IKB.models_buttons_edit_menu(
                models=models,
                filter_id=filter_id,
                current_model=callback_data.model or 'No selected'
            )
        )


    async def edit_typegines(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)

        typengines = await get_typengines(url=filter_data.get('url') + 'search/')
        if not typengines:
            return await call.message.edit_text(f"no typengine")

        await state.update_data(typengines=typengines)

        return await call.message.edit_text(
            f"Select body types for {filter_data.get('name_car')} (you can select multiplate):\n\nSelected: {', '.join(filter_data.get('typengines', [])) or 'No selected'}",
            reply_markup=await IKB.typengine_buttons_edit_menu(typengines=typengines, filter_id=data.get('filter_id'), selected_typengines=filter_data.get('typengines') or []))

    
    async def get_new_typengines(self, call: CallbackQuery, callback_data: TypengineCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        typengines = data.get('typengines', [])
        filter_id = data.get('filter_id')
        filter_typengines = filter_data.get('typengines') or []
        filter_typengines.append(callback_data.typengine) if callback_data.typengine not in filter_typengines else filter_typengines.remove(callback_data.typengine)

        self.update_json_cars(
            new_data={"typengines": filter_typengines},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"typengines": filter_typengines},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["typengines"] = filter_typengines
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select type engine for {filter_data.get('name_car')} (you can select multiplate):\n\nSelected: {', '.join(filter_typengines) or 'No selected'}",
            reply_markup=await IKB.typengine_buttons_edit_menu(typengines=typengines, filter_id=data.get('filter_id'), selected_typengines=filter_typengines or []))

    
    async def edit_min_year(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        years = await get_years(url=filter_data.get('url') + 'search/')
        if not years:
            return await call.message.edit_text("no years")

        await state.update_data(years=years)

        return await call.message.edit_text(
            f"Select min. year for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('min_year') or 'No selected'}",
            reply_markup=await IKB.years_buttons_edit_menu(
                years=years, filter_id=data.get('filter_id'), current_value=filter_data.get('min_year') or 'No selected', action='edit_min_year')
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
        
        self.update_json_cars(
            new_data={"min_year": callback_data.year},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"min_year": callback_data.year},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["min_year"] = callback_data.year
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select min. year for {filter_data.get('name_car')}\n\nSelected: {min_year or 'No selected'}",
            reply_markup=await IKB.years_buttons_edit_menu(
                years=years, filter_id=data.get('filter_id'), current_value=callback_data.year or 'No selected', action='edit_min_year')
        )

    async def edit_max_year(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        years = await get_years(url=filter_data.get('url') + 'search/')
        if not years:
            return await call.message.edit_text("no years")

        await state.update_data(years=years)

        return await call.message.edit_text(
            f"Select max. year for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('max_year') or 'No selected'}",
            reply_markup=await IKB.years_buttons_edit_menu(
                years=years, filter_id=data.get('filter_id'), current_value=filter_data.get('max_year') or 'No selected', action='edit_max_year')
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
        
        self.update_json_cars(
            new_data={"max_year": callback_data.year},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"max_year": callback_data.year},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["max_year"] = callback_data.year
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select max. year for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('max_year') or 'No selected'}",
            reply_markup=await IKB.years_buttons_edit_menu(
                years=years, filter_id=data.get('filter_id'), current_value=callback_data.year or 'No selected', action='edit_min_year')
        )

    
    async def edit_min_displacement(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        displacements = await get_displacement_motor(url=filter_data.get('url'))
        if not displacements:
            return await call.message.edit_text("no displacement")

        await state.update_data(displacements=displacements)

        return await call.message.edit_text(
            f"Select min. displacements for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('min_displacement') or 'No selected'}",
            reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements, filter_id=data.get('filter_id'), current_value=filter_data.get('min_displacement') or 'No selected', action='edit_min_displacement')
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
        
        self.update_json_cars(
            new_data={"min_displacement": callback_data.displacement},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"min_displacement": callback_data.displacement},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["min_displacement"] = callback_data.displacement
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select min. displacements for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('min_displacement') or 'No selected'}",
            reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements, filter_id=data.get('filter_id'), current_value=callback_data.displacement or 'No selected', action='edit_min_displacement')
        )

    
    async def edit_max_displacement(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        displacements = await get_displacement_motor(url=filter_data.get('url'))
        if not displacements:
            return await call.message.edit_text("no displacement")

        await state.update_data(displacements=displacements)

        return await call.message.edit_text(
            f"Select max. displacements for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('max_displacement') or 'No selected'}",
            reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements, filter_id=data.get('filter_id'), current_value=filter_data.get('max_displacement') or 'No selected', action='edit_max_displacement')
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
        
        self.update_json_cars(
            new_data={"max_displacement": callback_data.displacement},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"max_displacement": callback_data.displacement},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["max_displacement"] = callback_data.displacement
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select max. displacements for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('max_displacement') or 'No selected'}",
            reply_markup=await IKB.displacement_buttons_edit_menu(
                displacements=displacements, filter_id=data.get('filter_id'), current_value=callback_data.displacement or 'No selected', action='edit_max_displacement')
        )

    
    async def edit_gearbox(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)
        
        gearbox = await get_gearbox(url=filter_data.get('url') + 'search/')
        if not gearbox:
            return await call.message.edit_text(f"no gearbox")

        await state.update_data(gearbox=gearbox)

        return await call.message.edit_text(
            f"Select gearbox for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('gearbox') or 'No selected'}",
            reply_markup=await IKB.gerabox_buttons_edit_menu(geraboxes=gearbox, filter_id=data.get('filter_id'), current_value=filter_data.get('gearbox') or 'No selected'))

    
    async def get_new_gearbox(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        await call.answer('')

        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        gearboxes = data.get('gearbox', [])
        filter_id = data.get('filter_id')
        gearbox = filter_data.get('gearbox', None)

        if callback_data.gearbox == gearbox:
            return
        
        self.update_json_cars(
            new_data={"gearbox": callback_data.gearbox},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"gearbox": callback_data.gearbox},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["gearbox"] = callback_data.gearbox
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select gearbox for {filter_data.get('name_car')}\n\nSelected: {filter_data.get('gearbox') or 'No selected'}",
            reply_markup=await IKB.gerabox_buttons_edit_menu(geraboxes=gearboxes, filter_id=data.get('filter_id'), current_value=callback_data.gearbox or 'No selected'))

    
    async def edit_bodytypes(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', None)

        bodytypes = await get_bodytype(url=filter_data.get('url') + 'search/')
        if not bodytypes:
            return await call.message.edit_text(f"no bodytypes")

        await state.update_data(bodytypes=bodytypes)

        return await call.message.edit_text(
            f"Select body types for {filter_data.get('name_car')} (you can select multiplate):\n\nSelected: {', '.join(filter_data.get('bodytypes', [])) or 'No selected'}",
            reply_markup=await IKB.bodytype_buttons_edit_menu(bodytypes=bodytypes, filter_id=data.get('filter_id'), selected_bodytypes=filter_data.get('bodytypes') or []))

    
    async def get_new_bodytypes(self, call: CallbackQuery, callback_data: BodytypeCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        bodytypes = data.get('bodytypes', [])
        filter_id = data.get('filter_id')
        filter_bodytypes = filter_data.get('bodytypes') or []
        filter_bodytypes.append(callback_data.bodytype) if callback_data.bodytype not in filter_bodytypes else filter_bodytypes.remove(callback_data.bodytype)

        self.update_json_cars(
            new_data={"bodytypes": filter_bodytypes},
            uid=call.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"bodytypes": filter_bodytypes},
            uid=call.from_user.id,
            filter_id=filter_id
        )

        filter_data["bodytypes"] = filter_bodytypes
        await state.update_data(filter_data=filter_data)

        return await call.message.edit_text(
            f"Select body types for {filter_data.get('name_car')} (you can select multiplate):\n\nSelected: {', '.join(filter_bodytypes) or 'No selected'}",
            reply_markup=await IKB.bodytype_buttons_edit_menu(bodytypes=bodytypes, filter_id=filter_id, selected_bodytypes=filter_bodytypes or []))

    
    async def edit_min_price(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.set_state(EditFilterCar.MIN_PRICE)

        return await call.message.edit_text("Please enter the minimum price (Send 0 to skip minimum price):")

    
    async def get_new_min_price(self, m: Message, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        filter_id = data.get('filter_id')

        self.update_json_cars(
            new_data={"min_price": int(m.text)},
            uid=m.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"min_price": int(m.text)},
            uid=m.from_user.id,
            filter_id=filter_id
        )

        filter_data["min_price"] = int(m.text)
        await state.update_data(filter_data=filter_data)

        await m.answer(f"Minimum price successfully updated!")

        return await m.answer(f'You selected: {filter_data.get("name_car")}. Select what you want to change.', reply_markup=await IKB.edit_filter_menu(
            filter_id=filter_id, filters_data=filter_data
        ))

    
    async def edit_max_price(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.set_state(EditFilterCar.MAX_PRICE)

        return await call.message.edit_text("Please enter the maximum price (Send 0 to skip minimum price):")

    
    async def get_new_max_price(self, m: Message, state: FSMContext) -> Message:
        data = await state.get_data()
        filter_data = data.get('filter_data', {})
        filter_id = data.get('filter_id')

        self.update_json_cars(
            new_data={"max_price": int(m.text)},
            uid=m.from_user.id,
            filter_id=filter_id
        )
        self.update_json_threads(
            new_data={"max_price": int(m.text)},
            uid=m.from_user.id,
            filter_id=filter_id
        )

        filter_data["max_price"] = int(m.text)
        await state.update_data(filter_data=filter_data)

        await m.answer(f"Maximum price successfully updated!")

        return await m.answer(f'You selected: {filter_data.get("name_car")}. Select what you want to change.', reply_markup=await IKB.edit_filter_menu(
            filter_id=filter_id, filters_data=filter_data
        ))