from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.keyboards.callbackdata import *
from manager import thread_manager


class Ikb:
    @staticmethod
    async def main_menu() -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        menu.button(text="🚗 Cars", callback_data='cars')
        menu.button(text="📝 My Filters", callback_data='filters')

        return menu.adjust(1).as_markup()


    @staticmethod
    async def cars_buttons_menu(list_cars: list[dict]) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for data_car in list_cars:
            menu.button(text=data_car.get('car', None), callback_data=CarsCallback(action='car', name_car=data_car.get('car', None), url_car=data_car.get('url', None)))

        return menu.adjust(3).as_markup()

    
    @staticmethod
    async def models_buttons_menu(models: list[str]) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for model in models:
            menu.button(text=model, callback_data=ModelsCallback(action='car_models', model=model))

        menu.adjust(3)
        menu.row(InlineKeyboardButton(text="Skip >>", callback_data=ModelsCallback(action='car_models', model=None).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def years_buttons_menu(years: list[str], action: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for year in years:
            menu.button(text=year, callback_data=YearsCallback(action=action, year=year))

        menu.adjust(3)
        menu.row(InlineKeyboardButton(text="Skip >>", callback_data=YearsCallback(action=action, year=None).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def displacement_buttons_menu(displacements: list[str], action: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for displacement in displacements:
            menu.button(text=displacement, callback_data=DisplacementCallback(action=action, displacement=displacement))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Skip >>", callback_data=DisplacementCallback(action=action, displacement=None).pack()))

        return menu.as_markup()
    

    @staticmethod
    async def typengine_buttons_menu(typengines: list[str], selected_typengines: list[str] | None) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for typengine in typengines:
            selected = typengine in (selected_typengines or [])
            text = f'• {typengine}' if selected else typengine

            menu.button(text=text, callback_data=TypengineCallback(action="typengine", typengine=typengine, selected=selected))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Next >", callback_data=TypengineCallback(action="typengine", typengine=None).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def gerabox_buttons_menu(geraboxes: list[str]) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for gearbox in geraboxes:
            menu.button(text=gearbox, callback_data=GearboxCallback(action="gearbox", gearbox=gearbox))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Skip >>", callback_data=GearboxCallback(action="gearbox", gearbox=None).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def bodytype_buttons_menu(bodytypes: list[str], selected_bodytypes: list[str] | None) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for bodytype in bodytypes:
            selected = bodytype in (selected_bodytypes or [])
            text = f'• {bodytype}' if selected else bodytype
            menu.button(text=text, callback_data=BodytypeCallback(action="bodytype", bodytype=bodytype))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Next >", callback_data=BodytypeCallback(action="bodytype", bodytype=None).pack()))

        return menu.as_markup()
    

    @staticmethod
    async def inspection_buttons_menu(inspections: list[str]) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for inspection in inspections:
            menu.button(text=inspection, callback_data=InspectionCallback(action="inspection", inspection=inspection))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Skip >>", callback_data=InspectionCallback(action="inspection", inspection=None).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def final_menu() -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        menu.button(text="Approve", callback_data='approve')
        menu.button(text="Repeat", callback_data='repeat')

        return menu.as_markup()


    @staticmethod
    async def filters_menu(filters: tuple[str, str, str], uid: int) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for filter_id, car, car_model in filters:
            emoji = '🔴' if filter_id not in thread_manager.get_active_filters(uid=uid) else '🟢'

            text = f'{emoji} {car} [{car_model}]' if car_model else f'{emoji} {car}'
            menu.button(text=text, callback_data=FiltersCallback(action="filter", filter_id=filter_id))

        menu.adjust(1)
        menu.row(InlineKeyboardButton(text="Back <<", callback_data="back_main_menu"))

        return menu.as_markup()

    
    @staticmethod
    async def filter_menu(filter_id: str, uid: int) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        if filter_id not in thread_manager.get_active_filters(uid=uid):
            menu.button(text="Turn on 🟢", callback_data=FiltersCallback(action='on_filter', filter_id=filter_id))
        else:
            menu.button(text="Turn off 🔴", callback_data=FiltersCallback(action='off_filter', filter_id=filter_id))

        menu.button(text="❌ Delete filter", callback_data=FiltersCallback(action="delete_filter", filter_id=filter_id))
        menu.button(text="📝 Edit filter", callback_data=FiltersCallback(action="edit_filter", filter_id=filter_id))
        menu.button(text="Back >>", callback_data='back_filters')

        return menu.adjust(1).as_markup()

    
    @staticmethod
    async def edit_filter_menu(filter_id: str, filters_data: dict) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        fields = [
            "model", "min_year", "max_year", "min_price", "max_price", "min_displacement", "max_displacement", "typengines", "gearbox", "bodytypes"
        ]

        for field in fields:
            value = filters_data.get(field)
            if isinstance(value, list):
                value = ", ".join(value)
            value = value or "No selected"

            menu.button(text=f"{field.replace('_', ' ').title()}: {value}", callback_data=f'edit_{field}')
        
        menu.button(text="Back filter >>", callback_data=FiltersCallback(action="back_filter", filter_id=filter_id))

        menu.adjust(1)
        return menu.as_markup()

    
    @staticmethod
    async def models_buttons_edit_menu(models: list[str], filter_id: str, current_model: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for model in models:
            if current_model and model == current_model:
                text = f'• {model}'
            else:
                text = model

            menu.button(text=text, callback_data=ModelsCallback(action='edit_model', model=model))

        menu.adjust(3)
        
        if current_model != 'No selected':
            menu.row(InlineKeyboardButton(text="Remove ❌", callback_data=ModelsCallback(action='edit_model', model=None).pack()))

        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def typengine_buttons_edit_menu(typengines: list[str], filter_id: str, selected_typengines: list[str] | None) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for typengine in typengines:
            selected = typengine in (selected_typengines or [])
            text = f'• {typengine}' if selected else typengine

            menu.button(text=text, callback_data=TypengineCallback(action="edit_typengine", typengine=typengine))

        menu.adjust(1)
        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def years_buttons_edit_menu(years: list[str], filter_id: str, action: str, current_value: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for year in years:
            if current_value and year == current_value:
                text = f'• {year}'
            else:
                text = year
            menu.button(text=text, callback_data=YearsCallback(action=action, year=year))

        menu.adjust(4)

        if current_value != 'No selected':
            menu.row(InlineKeyboardButton(text="Remove ❌", callback_data=YearsCallback(action=action, year=None).pack()))

        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def displacement_buttons_edit_menu(displacements: list[str], filter_id: str, action: str, current_value: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for displacement in displacements:
            if current_value and displacement == current_value:
                text = f'• {displacement}'
            else:
                text = displacement
            menu.button(text=text, callback_data=DisplacementCallback(action=action, displacement=displacement))

        menu.adjust(3)

        if current_value != 'No selected':
            menu.row(InlineKeyboardButton(text="Remove ❌", callback_data=DisplacementCallback(action=action, displacement=None).pack()))

        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def gerabox_buttons_edit_menu(geraboxes: list[str], filter_id: str, current_value: str) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for gearbox in geraboxes:
            if current_value and gearbox == current_value:
                text = f'• {gearbox}'
            else:
                text = gearbox
            menu.button(text=text, callback_data=GearboxCallback(action="edit_gearbox", gearbox=gearbox))

        menu.adjust(2)
        if current_value != 'No selected':
            menu.row(InlineKeyboardButton(text="Remove ❌", callback_data=GearboxCallback(action='edit_gearbox', gearbox=None).pack()))

        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()

    
    @staticmethod
    async def bodytype_buttons_edit_menu(bodytypes: list[str], filter_id: str, selected_bodytypes: list[str] | None) -> InlineKeyboardBuilder:
        menu = InlineKeyboardBuilder()

        for bodytype in bodytypes:
            selected = bodytype in (selected_bodytypes or [])
            text = f'• {bodytype}' if selected else bodytype
            menu.button(text=text, callback_data=BodytypeCallback(action="edit_bodytype", bodytype=bodytype))

        menu.adjust(2)
        menu.row(InlineKeyboardButton(text="Back edit menu >>", callback_data=FiltersCallback(action="back_edit_menu", filter_id=filter_id).pack()))

        return menu.as_markup()