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
        await state.update_data(
            data={
                "uid": call.from_user.id,
                "name_car": name_car,
                "url": f"{base_url}{callback_data.url_car}"
            }
        )

        car_map = {
            "BMW": [
                "1 Series", "2 Series", "3 Series", "4 Series", "5 Series",
                "6 Series", "7 Series", "8 Series", "M Series",
                "X Series", "Z Series", "i Series"
            ],
            "Mercedes": [
                "A-Class", "B-Class", "C-Class", "CL-Class", "CLA-Class",
                "CLK-Class", "CLS-Class", "E-Class", "G-Class", "GL-Class",
                "GLA-Class", "GLB-Class", "GLC-Class", "GLE-Class", "GLK-Class",
                "GLS-Class", "ML-Class", "R-Class", "S-Class", "SL-Class",
                "SLK-Class", "V-Class", "X-Class", "Mercedes-Benz", "Citan", "Sprinter", "Vaneo", "Viano", "Vito"
            ]
        }

        if name_car in car_map:
            models = car_map[name_car]
            text = (
                f"🚘 <b>{name_car}</b>\n\n"
                f"<i>Here are the available models:</i>\n"
                f"➡️ <u>Select one below</u>:"
            )
            return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_menu(models=models))

        models_cars = await get_models_cars(url=f"{base_url}{callback_data.url_car}search/")
        if not models_cars:
            return await call.message.edit_text("❌ <b>No models found</b>")

        text = (
            f"🚗 <b>{name_car}</b>\n\n"
            f"<i>Here are the available models:</i>\n"
            f"➡️ <u>Select one below</u>:"
        )
        return await call.message.edit_text(text, reply_markup=await IKB.models_buttons_menu(models=models_cars))

    
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

        if model_name and not selected_models:
            await state.update_data(models=model_name, model=model_name)

        years = await get_years(url=f"{base_url}search/")
        if not years:
            return await call.message.edit_text("❌ <b>No years available</b>")

        await state.update_data(years=years)

        text = (
            f"🚘 <b>Brand:</b> {car or '<i>Not selected</i>'}\n"
            f"📍 <b>Model/Series:</b> {model_name or '<i>Not selected</i>'}\n\n"
            f"📅 <u>Please select a minimum year</u>:"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_menu(years=years, action="car_years_min"))

    
    async def get_year_min(self, call: CallbackQuery, callback_data: YearsCallback,  state: FSMContext) -> Message:
        data = await state.get_data()
        years = data.get('years', [])
        min_year = callback_data.year
        await state.update_data(min_year=min_year)

        if min_year is not None:
            filtered_years = [year for year in years if year > min_year] or [min_year]
        else:
            filtered_years = years

        text = (
            f"📅 <b>Minimum year selected:</b> {min_year or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Now select the maximum year</u>, or skip this step."
        )

        return await call.message.edit_text(text, reply_markup=await IKB.years_buttons_menu(years=filtered_years, action="car_years_max"))

    
    async def get_year_max(self, call: CallbackQuery, callback_data: YearsCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        model_name = data.get("model") or "<i>Not selected</i>"
        max_year = callback_data.year
        await state.update_data(max_year=max_year)

        displacements = await get_displacement_motor(url=data.get("url", None))
        if not displacements:
            return await call.message.edit_text("❌ <b>No displacement data available</b>", parse_mode="HTML")
        
        await state.update_data(displacements=displacements, years=None)

        text = (
            f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
            f"📍 <b>Model:</b> {model_name}\n"
            f"📅 <b>Minimum year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
            f"📅 <b>Maximum year:</b> {max_year or '<i>Not selected</i>'}\n\n"
            f"⚙️ <u>Please select the engine displacement</u>:"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.displacement_buttons_menu(displacements=displacements, action="min_displacement"))
    

    async def get_displacement_min(self, call: CallbackQuery, callback_data: DisplacementCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        displacements = data.get("displacements", [])
        min_displacement = callback_data.displacement
        await state.update_data(min_displacement=min_displacement)

        if min_displacement is not None:
            filtered_displacement = [d for d in displacements if d > min_displacement] or [min_displacement]
        else:
            filtered_displacement = displacements

        text = (
            f"⚙️ <b>Minimum engine capacity selected:</b> {min_displacement or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Please select the maximum engine capacity</u>:\n\n"
            f"🚘 <b>Brand:</b> {data.get('name_car') or '<i>Not selected</i>'}\n"
            f"📍 <b>Model:</b> {data.get('model') or '<i>Not selected</i>'}\n"
            f"📅 <b>Minimum Year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
            f"📅 <b>Maximum Year:</b> {data.get('max_year') or '<i>Not selected</i>'}\n"
            f"🔧 <b>Minimum Engine Volume:</b> {min_displacement or '<i>Not selected</i>'}"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.displacement_buttons_menu(displacements=filtered_displacement, action="max_displacement"))


    async def get_displacement_max(self, call: CallbackQuery, callback_data: DisplacementCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        model_name = data.get("model") or "<i>Not selected</i>"
        max_displacement = callback_data.displacement
        await state.update_data(max_displacement=max_displacement)

        typengines = await get_typengines(url=f"{data.get('url', None)}search/")
        if not typengines:
            return await call.message.edit_text("❌ <b>No engine types available</b>", parse_mode="HTML")

        await state.update_data(displacements=None, typengines=[], all_typengines=typengines)

        text = (
            f"🔧 <b>Maximum engine capacity selected:</b> {max_displacement or '<i>Not selected</i>'}\n\n"
            f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
            f"📍 <b>Model:</b> {model_name}\n"
            f"📅 <b>Minimum Year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
            f"📅 <b>Maximum Year:</b> {data.get('max_year') or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Minimum Engine Volume:</b> {data.get('min_displacement') or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Maximum Engine Volume:</b> {max_displacement or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Please select the engine type</u> (or skip this step):"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.typengine_buttons_menu(typengines=typengines, selected_typengines=None))


    async def get_typengine(self, call: CallbackQuery, callback_data: TypengineCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        typengines = data.get("typengines", [])
        all_typengines = data.get("all_typengines", [])
        typengine = callback_data.typengine

        if typengine:
            if typengine not in typengines:
                typengines.append(typengine)
            else:
                typengines.remove(typengine)

            await state.update_data(typengines=typengines)

            text = (
                f"⚙️ <b>Engine type selected:</b> {', '.join(typengines) or '<i>Not selected</i>'}\n\n"
                f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
                f"📍 <b>Model:</b> {data.get('model') or '<i>Not selected</i>'}\n"
                f"📅 <b>Minimum Year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
                f"📅 <b>Maximum Year:</b> {data.get('max_year') or '<i>Not selected</i>'}\n"
                f"🔧 <b>Minimum Engine Volume:</b> {data.get('min_displacement') or '<i>Not selected</i>'}\n"
                f"🔧 <b>Maximum Engine Volume:</b> {data.get('max_displacement') or '<i>Not selected</i>'}\n\n"
                f"➡️ <u>Please select the engine type</u> (or skip this step):"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.typengine_buttons_menu(typengines=all_typengines, selected_typengines=typengines))

        else:
            await state.update_data(all_typengines=None)

            gearbox = await get_gearbox(url=f"{data.get('url', None)}search/")
            if not gearbox:
                return await call.message.edit_text("❌ <b>No gearbox data available</b>")

            text = (
                f"⚙️ <b>Engine type selected:</b> {', '.join(typengines) or '<i>Not selected</i>'}\n\n"
                f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
                f"📍 <b>Model:</b> {data.get('model') or '<i>Not selected</i>'}\n"
                f"📅 <b>Minimum Year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
                f"📅 <b>Maximum Year:</b> {data.get('max_year') or '<i>Not selected</i>'}\n"
                f"🔧 <b>Minimum Engine Volume:</b> {data.get('min_displacement') or '<i>Not selected</i>'}\n"
                f"🔧 <b>Maximum Engine Volume:</b> {data.get('max_displacement') or '<i>Not selected</i>'}\n\n"
                f"⚙️ <u>Select the type of gearbox</u> (or skip this step):"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.gerabox_buttons_menu(geraboxes=gearbox))

    
    async def get_gerabox(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        gearbox = callback_data.gearbox
        await state.update_data(gearbox=gearbox)

        bodytype = await get_bodytype(url=f"{data.get('url', None)}search/")
        if not bodytype:
            return await call.message.edit_text("❌ <b>No body types available</b>")
        
        await state.update_data(all_bodytypes=bodytype, bodytypes=[])

        text = (
            f"⚙️ <b>Gearbox type selected:</b> {gearbox or '<i>Not selected</i>'}\n\n"
            f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
            f"📍 <b>Model:</b> {data.get('model') or '<i>Not selected</i>'}\n"
            f"📅 <b>Minimum Year:</b> {data.get('min_year') or '<i>Not selected</i>'}\n"
            f"📅 <b>Maximum Year:</b> {data.get('max_year') or '<i>Not selected</i>'}\n"
            f"🔧 <b>Minimum Engine Volume:</b> {data.get('min_displacement') or '<i>Not selected</i>'}\n"
            f"🔧 <b>Maximum Engine Volume:</b> {data.get('max_displacement') or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Engine Type:</b> {', '.join(data.get('typengines', [])) or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Gearbox:</b> {gearbox or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Please select the body type</u> (or skip this step):"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.bodytype_buttons_menu(bodytypes=bodytype, selected_bodytypes=None))

    
    async def get_bodytype(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        data = await state.get_data()
        all_bodytypes = data.get("all_bodytypes", [])
        bodytypes = data.get("bodytypes", [])
        bodytype = callback_data.bodytype

        if bodytype:
            if bodytype not in bodytypes:
                bodytypes.append(bodytype)
            else:
                bodytypes.remove(bodytype)

            await state.update_data(bodytypes=bodytypes)

            text = (
                f"🚙 <b>Body type selected:</b> {', '.join(bodytypes) or '<i>Not selected</i>'}\n\n"
                f"➡️ <u>Please select the type of inspection</u> (or skip this step):"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.bodytype_buttons_menu(bodytypes=all_bodytypes, selected_bodytypes=bodytypes))

        else:
            inspections = await get_inspection(url=f"{data.get('url', None)}search/")
            if not inspections:
                return await call.message.edit_text("❌ <b>No inspections available</b>")

            await state.update_data(all_bodytypes=None)

            text = (
                f"🚙 <b>Body type selected:</b> {', '.join(bodytypes) or '<i>Not selected</i>'}\n\n"
                f"➡️ <u>Please select the type of inspection</u> (or skip this step):"
            )

            return await call.message.edit_text(text, reply_markup=await IKB.inspection_buttons_menu(inspections=inspections))


    async def get_inspection(self, call: CallbackQuery, callback_data: GearboxCallback, state: FSMContext) -> Message:
        await state.update_data(inspection=callback_data.inspection)
        await state.set_state(AddFilterCar.MIN_PRICE)

        text = (
            f"🛠 <b>Inspection type selected:</b> {callback_data.inspection or '<i>Not selected</i>'}\n\n"
            f"💰 <u>Please enter the minimum price</u>\n"
            f"(Send <b>0</b> to skip minimum price)"
        )

        return await call.message.edit_text(text)

    
    async def get_min_price(self, m: Message, state: FSMContext) -> Message:
        await state.update_data(min_price=int(m.text) or None)
        await state.set_state(AddFilterCar.MAX_PRICE)

        text = (
            f"💰 <b>Minimum price saved:</b> {m.text or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Please enter the maximum price</u>\n"
            f"(Send <b>0</b> to skip maximum price)"
        )

        return await m.answer(text)

    
    async def get_max_price(self, m: Message, state: FSMContext) -> Message:
        await state.update_data(max_price=int(m.text) or None)
        data = await state.get_data()

        text = (
            f"✅ <b>Your selection summary:</b>\n\n"
            f"🚘 <b>Brand:</b> {data.get('name_car', '<i>Not selected</i>')}\n"
            f"📍 <b>Model:</b> {data.get('model', '<i>Not selected</i>')}\n"
            f"💰 <b>Price:</b> {data.get('min_price') or '<i>Not selected</i>'} – {data.get('max_price') or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Engine type:</b> {', '.join(data.get('typengines', [])) or '<i>Not selected</i>'}\n"
            f"🔧 <b>Engine volume:</b> from {data.get('min_displacement') or '<i>Not selected</i>'} to {data.get('max_displacement') or '<i>Not selected</i>'}\n"
            f"⚙️ <b>Gearbox:</b> {data.get('gearbox') or '<i>Not selected</i>'}\n"
            f"📅 <b>Years:</b> from {data.get('min_year') or '<i>Not selected</i>'} to {data.get('max_year') or '<i>Not selected</i>'}\n"
            f"🚙 <b>Body:</b> {', '.join(data.get('bodytypes', [])) or '<i>Not selected</i>'}\n\n"
            f"➡️ <u>Click 'Approve' to proceed</u> or <u>'Repeat'</u> to fill out filters again."
        )

        return await m.answer(text, reply_markup=await IKB.final_menu())


    async def repeat(self, call: CallbackQuery) -> Message:
        list_cars = await get_list_cars()
        if not list_cars:
            return await call.message.answer("❌ <b>Error: no cars available</b>", parse_mode="HTML")

        text = (
            f"🚘 <b>Please choose a car brand</b>:\n"
            f"➡️ Select one from the list below:"
        )

        return await call.message.edit_text(text, reply_markup=await IKB.cars_buttons_menu(list_cars=list_cars))

    
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

        text = (
            f"✅ <b>Your data has been successfully saved!</b>\n\n"
            f"📂 Record ID: <code>{record_id}</code>\n"
            f"➡️ You can now proceed with the search."
        )

        return await call.message.edit_text(text)
