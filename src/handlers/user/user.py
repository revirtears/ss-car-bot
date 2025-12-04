import json
import uuid
from pathlib import Path

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, FSInputFile

from src.core.bot import SettingsBot
from src.keyboards.inline import Ikb as IKB
from src.keyboards.callbackdata import *

from request import *
from manager import thread_manager


base_url = 'https://www.ss.com'


class AddFilterCar(StatesGroup):
    MIN_PRICE = State()
    MAX_PRICE = State()


class ClientHandlers:
    def __init__(self, module: SettingsBot) -> None:
        self.bot = module.bot
        self.dp = module.dp
        self.cfg = module.config


    async def register_handlers(self):
        self.dp.message(CommandStart(), StateFilter("*"))(self.command_start)
        self.dp.callback_query(F.data == 'cars', StateFilter("*"))(self.get_cars)
        self.dp.callback_query(CarsCallback.filter(F.action == 'car'))(self.get_car)
        self.dp.callback_query(ModelsCallback.filter(F.action == 'car_models'))(self.get_model)
        self.dp.callback_query(YearsCallback.filter(F.action == 'car_years_min'))(self.get_year_min)
        self.dp.callback_query(YearsCallback.filter(F.action == 'car_years_max'))(self.get_year_max)
        self.dp.callback_query(DisplacementCallback.filter(F.action == 'min_displacement'))(self.get_displacement_min)
        self.dp.callback_query(DisplacementCallback.filter(F.action == 'max_displacement'))(self.get_displacement_max)
        self.dp.callback_query(TypengineCallback.filter(F.action == 'typengine'))(self.get_typengine)
        self.dp.callback_query(GearboxCallback.filter(F.action == 'gearbox'))(self.get_gerabox)
        self.dp.callback_query(BodytypeCallback.filter(F.action == 'bodytype'))(self.get_bodytype)
        self.dp.callback_query(InspectionCallback.filter(F.action == 'inspection'))(self.get_inspection)
        self.dp.message(F.text.isdigit(), StateFilter(AddFilterCar.MIN_PRICE))(self.get_min_price)
        self.dp.message(F.text.isdigit(), StateFilter(AddFilterCar.MAX_PRICE))(self.get_max_price)

        self.dp.callback_query(F.data == 'repeat', StateFilter("*"))(self.repeat)
        self.dp.callback_query(F.data == 'approve', StateFilter("*"))(self.approve)


    async def command_start(self, m: Message, state: FSMContext) -> Message:
        return await m.answer("Hello! 👋\n\nWelcome to the bot for finding ads!", reply_markup=await IKB.main_menu())

    
    async def get_cars(self, call: CallbackQuery, state: FSMContext) -> Message:
        await state.clear()

        list_cars = await get_list_cars()
        if not list_cars:
            return await call.message.answer("not found cars!")

        return await call.message.edit_text("<b>Select car:</b>", reply_markup=await IKB.cars_buttons_menu(list_cars=list_cars))


    async def get_car(self, call: CallbackQuery, callback_data: CarsCallback, state: FSMContext) -> Message:
        name_car = callback_data.name_car
        await state.update_data(data={"uid": call.from_user.id, "name_car": name_car, "url": f"{base_url}{callback_data.url_car}"})

        if name_car == "BMW":
            series = [
                "1 series", '2 series', '3 series', '4 series', '5 series', '6 series', '7 series', '8 series', 'M series', 'X series', 'Z series', 'i series'
            ]

            return await call.message.edit_text(
                "Here are the series for BMW:\nSelect a series:", reply_markup=await IKB.models_buttons_menu(models=[serie for serie in series])
            )
        
        elif name_car == 'Mercedes':
            classes = [
                "A-class", "B-class", "C-class", "CL-class", "CLA-class", "CLK-class", "CLS-class", "E-class", "G-class", "GL-clase", "GLA-class", "GLB-class", "GLC-class", "GLE-class", "GLK-clase", "GLS-class", "ML-class", "R-class", "S-class", "SL-class", "SLK-class", "V-class", "X-class", "Mercedes-benz"
            ]

            return await call.message.edit_text(
                "Here are the classes for Mercedes:\nSelect a class:", reply_markup=await IKB.models_buttons_menu(models=[class_id for class_id in classes])
            )
        
        else:
            models_cars = await get_models_cars(url=f"{base_url}{callback_data.url_car}search/")
            if not models_cars:
                return await call.message.edit_text("No models")

            return await call.message.edit_text(
                f"Here are the models for {name_car}:\nSelect a model:", reply_markup=await IKB.models_buttons_menu(models=models_cars)
            )

    
    async def get_model(self, call: CallbackQuery, callback_data: ModelsCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        model_name = callback_data.model
        car = data.get("name_car")
        base_url = data.get("url")

        selected_models = None
        if car in ("BMW", "Mercedes") and model_name:
            models = await get_models(url=base_url)
            if models:
                selected = models.get(model_name)
                if selected_models := selected:
                    await state.update_data(models=selected, model=model_name)

        if model_name:
            if not selected_models:
                await state.update_data(models=model_name, model=model_name)

        years = await get_years(url=f"{base_url}search/")
        if not years:
            return await call.message.edit_text("no years")

        await state.update_data(years=years)

        text = (
            f"You selected the brand: {car or 'No selected'}\n"
            f"You selected the model/series: {model_name or 'No selected'}\n"
            f"Please select a minimum year:"
        )

        return await call.message.edit_text(
            text,
            reply_markup=await IKB.years_buttons_menu(years=years, action="car_years_min")
        )

    
    async def get_year_min(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        years = data.get('years', [])
        min_year = callback_data.year
        await state.update_data(min_year=min_year)

        if min_year is not None:
            filtered_years = [year for year in years if year > min_year] or [min_year]
        else:
            filtered_years = years

        return await call.message.edit_text(
            (
                f"You selected minimum year: {min_year or 'No selected'}.\n"
                "Now select the maximum year, or skip this step."
            ), reply_markup=await IKB.years_buttons_menu(years=filtered_years, action='car_years_max')
        )

    
    async def get_year_max(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        model_name = data.get('model') or "No selected"
        max_year = callback_data.year
        await state.update_data(max_year=max_year)

        displacements = await get_displacement_motor(url=data.get('url', None))
        if not displacements:
            return await call.message.edit_text("no displacement")
        
        await state.update_data(displacements=displacements, years=None)
        return await call.message.edit_text(
            (
                f"You selected the brand: {data.get('name_car', 'No selected')}\n"
                f"You selected the model: {model_name}\n"
                f"Minimum year: {data.get('min_year', 'No selected')}\n"
                f"Maximum year: {max_year or 'No selected'}\n"
                f"Now, please select the engine displacement:"
            ), reply_markup=await IKB.displacement_buttons_menu(displacements=displacements, action='min_displacement')
        )
    

    async def get_displacement_min(self, call: CallbackQuery, callback_data: DisplacementCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        displacements = data.get('displacements', [])
        min_displacement = callback_data.displacement
        await state.update_data(min_displacement=min_displacement)

        if min_displacement is not None:
            filtered_displacement = [displacement for displacement in displacements if displacement > min_displacement] or [min_displacement]
        else:
            filtered_displacement = displacements

        return await call.message.edit_text(
            (
                f"You selected minimum engine capacity: {min_displacement}. Now, please select the maximum engine capacity.\n\n"
                f"Brand: {data.get('name_car', 'No selected')}\n"
                f"Model: {data.get('model', 'No selected')}\n"
                f"Minimum Year: {data.get('min_year', 'No selected')}\n"
                f"Maximum Year: {data.get('max_year', 'No selected')}\n"
                f"Minimum Engine Volume: {min_displacement or 'No selected'}\n"
            ), reply_markup=await IKB.displacement_buttons_menu(displacements=filtered_displacement, action='max_displacement')
        )
    

    async def get_displacement_max(self, call: CallbackQuery, callback_data: DisplacementCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        model_name = data.get('model') or "No selected"
        max_displacement = callback_data.displacement
        await state.update_data(max_displacement=max_displacement)

        typengines = await get_typengines(url=f"{data.get('url', None)}search/")
        if not typengines:
            return await call.message.edit_text(f"no typengine")

        await state.update_data(displacements=None, typengines=[], all_typengines=typengines)

        return await call.message.edit_text(
            (
                f"You selected maximum engine capacity: {max_displacement}.\n\n"
                f"Brand: {data.get('name_car', 'No selected')}\n"
                f"Model: {model_name}\n"
                f"Minimum Year: {data.get('min_year', 'No selected')}\n"
                f"Maximum Year: {data.get('max_year', 'No selected')}\n"
                f"Minimum Engine Volume: {data.get('min_displacement', 'No selected')}\n"
                f"Maximum Engine Volume: {max_displacement or 'No selected'}\n\n"
                f"Now, please select the engine type (or skip this step):"
            ), reply_markup=await IKB.typengine_buttons_menu(typengines=typengines, selected_typengines=None)
        )


    async def get_typengine(self, call: CallbackQuery, callback_data: TypengineCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        typengines = data.get('typengines', [])
        all_typengines = data.get('all_typengines', [])
        typengine = callback_data.typengine

        if typengine:
            if typengine not in typengines:
                typengines.append(typengine)
            else:
                typengines.remove(typengine)

            await state.update_data(typengines=typengines)

            return await call.message.edit_text(
                (
                    f"You selected engine type: {', '.join(typengines) or 'No selected'}!\n\n"
                    f"Brand: {data.get('name_car', 'No selected')}\n"
                    f"Model: {data.get('model') or 'No selected'}\n"
                    f"Minimum Year: {data.get('min_year', 'No selected')}\n"
                    f"Maximum Year: {data.get('max_year', 'No selected')}\n"
                    f"Minimum Engine Volume: {data.get('min_displacement', 'No selected')}\n"
                    f"Maximum Engine Volume: {data.get('max_displacement', 'No selected')}\n"
                    "Now, please select the engine type (or skip this step):"
                ), reply_markup=await IKB.typengine_buttons_menu(typengines=all_typengines, selected_typengines=typengines)
            )
        else:
            await state.update_data(all_typengines=None)

            gearbox = await get_gearbox(url=f"{data.get('url', None)}search/")
            if not gearbox:
                return await call.message.edit_text(f"no gearbox")

            return await call.message.edit_text(
                (
                    f"You selected engine type: {', '.join(typengines) or 'No selected'}!\n\n"
                    f"Brand: {data.get('name_car', 'No selected')}\n"
                    f"Model: {data.get('model') or 'No selected'}\n"
                    f"Minimum Year: {data.get('min_year', 'No selected')}\n"
                    f"Maximum Year: {data.get('max_year', 'No selected')}\n"
                    f"Minimum Engine Volume: {data.get('min_displacement', 'No selected')}\n"
                    f"Maximum Engine Volume: {data.get('max_displacement', 'No selected')}\n"
                    "Select the type of gearbox (or skip this step):"
                ), reply_markup=await IKB.gerabox_buttons_menu(geraboxes=gearbox)
            )

    
    async def get_gerabox(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        gearbox = callback_data.gearbox
        await state.update_data(gearbox=gearbox)

        bodytype = await get_bodytype(url=f"{data.get('url', None)}search/")
        if not bodytype:
            return await call.message.edit_text(f"no bodytype")
        
        await state.update_data(all_bodytypes=bodytype, bodytypes=[])

        return await call.message.edit_text(
            (
                f"You selected gearbox type: {gearbox or 'No selected'}.\n\n"
                f"Brand: {data.get('name_car', 'No selected')}\n"
                f"Model: {data.get('model') or 'No selected'}\n"
                f"Minimum Year: {data.get('min_year', 'No selected')}\n"
                f"Maximum Year: {data.get('max_year', 'No selected')}\n"
                f"Minimum Engine Volume: {data.get('min_displacement', 'No selected')}\n"
                f"Maximum Engine Volume: {data.get('max_displacement', 'No selected')}\n"
                f"Engine Type: {', '.join(data.get('typengines', [])) or 'No selected'}\n"
                f"Gearbox: {gearbox or 'No selected'}\n\n"
                "Select the type of body (or skip this step):"
            ), reply_markup=await IKB.bodytype_buttons_menu(bodytypes=bodytype, selected_bodytypes=None)
        )

    
    async def get_bodytype(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        all_bodytypes = data.get('all_bodytypes', [])
        bodytypes = data.get('bodytypes', None)
        bodytype = callback_data.bodytype
        if bodytype:
            if bodytype not in bodytypes:
                bodytypes.append(bodytype)
            else:
                bodytypes.remove(bodytype)

            await state.update_data(bodytypes=bodytypes)

            return await call.message.edit_text(
                (
                f"You selected body type: {', '.join(bodytypes) or 'No selected'}.\n\n"
                "Select the type of inspection (or skip this step):"
                ), reply_markup=await IKB.bodytype_buttons_menu(bodytypes=all_bodytypes, selected_bodytypes=bodytypes)
            )
        else:
            inspections = await get_inspection(url=f"{data.get('url', None)}search/")
            if not inspections:
                return await call.message.edit_text(f"no inspection")

            await state.update_data(all_bodytypes=None)

            return await call.message.edit_text(
                (
                f"You selected body type: {', '.join(bodytypes) or 'No selected'}.\n\n"
                "Select the type of inspection (or skip this step):"
                ), reply_markup=await IKB.inspection_buttons_menu(inspections=inspections)
            )


    async def get_inspection(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        await state.update_data(inspection=callback_data.inspection)
        await state.set_state(AddFilterCar.MIN_PRICE)

        return await call.message.edit_text("Please enter the minimum price (Send 0 to skip minimum price):")

    
    async def get_min_price(self, m: Message, state: FSMContext) -> Message:
        await state.update_data(min_price=int(m.text) or None)
        await state.set_state(AddFilterCar.MAX_PRICE)

        return await m.answer("Please enter the maximum price (Send 0 to skip maximum price):")

    
    async def get_max_price(self, m: Message, state: FSMContext) -> Message:
        await state.update_data(max_price=int(m.text) or None)
        data = await state.get_data()

        return await m.answer(
            ( 
                f"You selected <b>{data.get('name_car', 'No selected')}</b> <b>{data.get('model', 'No selected')}</b> with filters:\n"
                f"<b>Price:</b> {data.get('min_price', 'No selected')} - {data.get('max_price', 'No selected')}\n"
                f"<b>Type of engine:</b> {', '.join(data.get('typengines', [])) or 'No selected'} with volume: <b>from</b> {data.get('min_displacement', 'No selected')} <b>to</b> {data.get('max_displacement', 'No selected')}\n"
                f"<b>Gearbox:</b> {data.get('gearbox', 'No selected')}\n"
                f"<b>Years:</b> from <b>{data.get('min_year', 'No selected')}</b> to <b>{data.get('max_year', 'No selected')}</b>\n"
                f"<b>Body:</b> {', '.join(data.get('bodytypes', [])) or 'No selected'}\n\n"
                f"Click 'Approve' to proceed or 'Repeat' to fill out filters again"
            ), reply_markup=await IKB.final_menu()
        )


    async def repeat(self, call: CallbackQuery) -> Message:
        list_cars = await get_list_cars()
        if not list_cars:
            return await m.answer("error")

        return await call.message.edit_text("Choise cars:", reply_markup=await IKB.cars_buttons_menu(list_cars=list_cars))

    
    async def approve(self, call: CallbackQuery, state: FSMContext) -> Message:
        data = await state.get_data()

        file_path = Path("data_tasks/cars.json")
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                db = json.load(f)
        else:
            db = {}

        record_id = str(uuid.uuid4())
        db[record_id] = {k: v for k, v in data.items() if v is not None}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)

        thread_manager.start_threads(data_search={record_id: db[record_id]}, uid=call.from_user.id)

        return await call.message.edit_text("<b>Your data has been successfully saved!</b>")
