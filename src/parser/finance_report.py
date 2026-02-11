import logging
from datetime import datetime

from .models import WbPeriod
from . import utils
from .parsers_config import *


def parse_report_detail(data: list[dict]) -> list[dict]:
    if len(data) == 0:
        return []

    parsed: list[dict] = []

    for i, row in enumerate(data, start=1):
        parsed.append({
            "№": i,
            "Номер поставки": row.get("realizationreport_id"),
            "Предмет": row.get("subject_name"),
            "Код номенклатуры": row.get("nm_id"),
            "Бренд": row.get("brand_name"),
            "Артикул поставщика": row.get("sa_name"),
            "Название": "N/A",  # пока замокано
            "Размер": row.get("ts_name"),
            "Баркод": row.get("barcode"),
            "Тип документа": row.get("doc_type_name"),
            "Обоснование для оплаты": row.get("supplier_oper_name"),
            "Дата заказа покупателем": row.get("order_dt"),
            "Дата продажи": row.get("sale_dt"),
            "Кол-во": row.get("quantity"),
            "Цена розничная": row.get("retail_price"),
            "Вайлдберриз реализовал Товар (Пр)": row.get("retail_amount"),
            "Согласованный продуктовый дисконт %": row.get("product_discount_for_report"),
            "Промокод %": row.get("sale_price_promocode_discount_prc"),
            "Итоговая согласованная скидка %": row.get("sale_percent"),
            "Цена розничная с учетом согласованной скидки": row.get("retail_price_withdisc_rub"),
            "Размер снижения кВВ из-за рейтинга %": row.get("sup_rating_prc_up"),
            "Размер изменения кВВ из-за акции %": row.get("ppvz_kvw_prc"),
            "Скидка постоянного Покупателя (СПП) %": row.get("ppvz_spp_prc"),
            "Размер кВВ %": row.get("ppvz_kvw_prc_base"),
            "Размер кВВ без НДС % Базовый": row.get("ppvz_kvw_prc_base"),
            "Итоговый кВВ без НДС %": row.get("ppvz_kvw_prc"),
            "Вознаграждение с продаж до вычета услуг поверенного без НДС": row.get("ppvz_sales_commission"),
            "Возмещение за выдачу и возврат товаров на ПВЗ": row.get("ppvz_reward"),
            "Эквайринг / Комиссии за организацию платежей": row.get("acquiring_fee"),
            "Размер комиссии за эквайринг / Комиссии за организацию платежей %": row.get("acquiring_percent"),
            "Тип платежа за Эквайринг / Комиссии за организацию платежей": row.get("payment_processing"),
            "Вознаграждение Вайлдберриз (ВВ) без НДС": row.get("ppvz_vw"),
            "НДС с Вознаграждения Вайлдберриз": row.get("ppvz_vw_nds"),
            "К перечислению Продавцу за реализованный Товар": row.get("ppvz_for_pay"),
            "Количество доставок": row.get("delivery_amount"),
            "Количество возврата": row.get("return_amount"),
            "Услуги по доставке товара покупателю": row.get("delivery_rub"),
            "Дата начала действия фиксации": row.get("fix_tariff_date_from"),
            "Дата конца действия фиксации": row.get("fix_tariff_date_to"),
            "Признак услуги платной доставки": row.get("delivery_amount") > 0,
            "Общая сумма штрафов": row.get("penalty"),
            "Корректировка Вознаграждения Вайлдберриз (ВВ)": row.get("additional_payment"),
            "Виды логистики, штрафов и корректировок ВВ": row.get("bonus_type_name"),
            "Стикер МП": row.get("sticker_id"),
            "Наименование банка-эквайера": row.get("acquiring_bank"),
            "Номер офиса": row.get("ppvz_office_id"),
            "Наименование офиса доставки": row.get("ppvz_office_name"),
            "ИНН партнера": row.get("ppvz_inn"),
            "Партнер": row.get("ppvz_supplier_name"),
            "Склад": row.get("office_name"),
            "Страна": row.get("site_country"),
            "Тип коробов": row.get("gi_box_type_name"),
            "Номер таможенной декларации": row.get("declaration_number"),
            "Номер сборочного задания": row.get("assembly_id"),
            "Код маркировки": row.get("kiz"),
            "ШК": row.get("shk_id"),
            "Srid": row.get("srid"),
            "Возмещение издержек по перевозке / по складским операциям с товаром": row.get("rebill_logistic_cost"),
            "Организатор перевозки": row.get("rebill_logistic_org"),
            "Хранение": row.get("storage_fee"),
            "Удержания": row.get("deduction"),
            "Операции на приемке": row.get("acceptance"),
            "Фиксированный коэффициент склада по поставке": row.get("dlv_prc"),
        })
    return parsed


def get_report_by_period(token: str, date_from: datetime, date_to: datetime) -> list[dict]:
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")

    url = f"{WB_REPORT_URL}?dateFrom={date_from_str}&dateTo={date_to_str}"
    headers = utils.get_auth_header(token)

    response = utils.api_get(
        url, headers, FIN_REPORT_ATTEMPTS, FIN_REPORT_WAIT_TIME)
    if not response:
        logging.error("Empty response from WB API")
        return []
    return parse_report_detail(response)


def write_finance_report(spreadsheet_id: str, token: str, sheet_name: str, period: WbPeriod):
    report_entries = get_report_by_period(
        token, period.start, period.end)

    range_ = f"{sheet_name}!{FIN_REPORT_RANGE}"
    # with open("output.csv", "w") as file:
    #     headers = list(report_entries[0].keys())
    #     values = [headers] + [list(row.values()) for row in report_entries]
    #     for row in values:
    #         file.write(";".join([str(i) for i in row]) + "\n")
    utils.write_entries_to_google(spreadsheet_id, range_, report_entries)
