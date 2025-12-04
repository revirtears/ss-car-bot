from typing import Optional
from aiogram.filters.callback_data import CallbackData


class CarsCallback(CallbackData, prefix="cars"):
    action: str
    name_car: Optional[str]
    url_car: Optional[str]


class ModelsCallback(CallbackData, prefix="models"):
    action: str
    model: Optional[str]


class YearsCallback(CallbackData, prefix="years"):
    action: str
    year: Optional[str]


class DisplacementCallback(CallbackData, prefix="displacement"):
    action: str
    displacement: Optional[str]


class TypengineCallback(CallbackData, prefix="typengine"):
    action: str
    typengine: Optional[str]


class GearboxCallback(CallbackData, prefix="gearbox"):
    action: str
    gearbox: Optional[str]


class BodytypeCallback(CallbackData, prefix="bodytype"):
    action: str
    bodytype: Optional[str]


class InspectionCallback(CallbackData, prefix="inspection"):
    action: str
    inspection: Optional[str]


class FiltersCallback(CallbackData, prefix="filters"):
    action: str
    filter_id: str
