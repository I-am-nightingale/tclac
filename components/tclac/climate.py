from esphome import automation, pins
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import climate, uart
from esphome.const import (
    CONF_ID,
    CONF_LEVEL,
    CONF_BEEPER,
    CONF_VISUAL,
    CONF_MAX_TEMPERATURE,
    CONF_MIN_TEMPERATURE,
    CONF_SUPPORTED_MODES,
    CONF_TEMPERATURE_STEP,
    CONF_SUPPORTED_PRESETS,
    CONF_TARGET_TEMPERATURE,
    CONF_SUPPORTED_FAN_MODES,
    CONF_SUPPORTED_SWING_MODES,
)

from esphome.components.climate import (
    ClimateMode,
    ClimatePreset,
    ClimateSwingMode,
    CONF_CURRENT_TEMPERATURE,
)

AUTO_LOAD = ["climate"]
CODEOWNERS = ["@I-am-nightingale", "@xaxexa", "@junkfix"]
DEPENDENCIES = ["climate", "uart"]

TCLAC_MIN_TEMPERATURE = 16.0
TCLAC_MAX_TEMPERATURE = 31.0
TCLAC_TARGET_TEMPERATURE_STEP = 1.0
TCLAC_CURRENT_TEMPERATURE_STEP = 1.0

CONF_RX_LED = "rx_led"
CONF_TX_LED = "tx_led"
CONF_DISPLAY = "show_display"
CONF_FORCE_MODE = "force_mode"
CONF_VERTICAL_AIRFLOW = "vertical_airflow"
CONF_MODULE_DISPLAY = "show_module_display"
CONF_HORIZONTAL_AIRFLOW = "horizontal_airflow"
CONF_VERTICAL_SWING_MODE = "vertical_swing_mode"
CONF_HORIZONTAL_SWING_MODE = "horizontal_swing_mode"

tclac_ns = cg.esphome_ns.namespace("tclac")
tclacClimate = tclac_ns.class_("tclacClimate", uart.UARTDevice, climate.Climate, cg.PollingComponent)

SUPPORTED_FAN_MODES_OPTIONS = {
    "AUTO": ClimateMode.CLIMATE_FAN_AUTO,  # Доступен всегда
    "QUIET": ClimateMode.CLIMATE_FAN_QUIET,
    "LOW": ClimateMode.CLIMATE_FAN_LOW,
    "MIDDLE": ClimateMode.CLIMATE_FAN_MIDDLE,
    "MEDIUM": ClimateMode.CLIMATE_FAN_MEDIUM,
    "HIGH": ClimateMode.CLIMATE_FAN_HIGH,
    "FOCUS": ClimateMode.CLIMATE_FAN_FOCUS,
    "DIFFUSE": ClimateMode.CLIMATE_FAN_DIFFUSE,
}

SUPPORTED_SWING_MODES_OPTIONS = {
    "OFF": ClimateSwingMode.CLIMATE_SWING_OFF,  # Доступен всегда
    "VERTICAL": ClimateSwingMode.CLIMATE_SWING_VERTICAL,
    "HORIZONTAL": ClimateSwingMode.CLIMATE_SWING_HORIZONTAL,
    "BOTH": ClimateSwingMode.CLIMATE_SWING_BOTH,
}

SUPPORTED_CLIMATE_MODES_OPTIONS = {
    "OFF": ClimateMode.CLIMATE_MODE_OFF,  # Доступен всегда
    "AUTO": ClimateMode.CLIMATE_MODE_AUTO,  # Доступен всегда
    "COOL": ClimateMode.CLIMATE_MODE_COOL,
    "HEAT": ClimateMode.CLIMATE_MODE_HEAT,
    "DRY": ClimateMode.CLIMATE_MODE_DRY,
    "FAN_ONLY": ClimateMode.CLIMATE_MODE_FAN_ONLY,
}

SUPPORTED_CLIMATE_PRESETS_OPTIONS = {
    "NONE": ClimatePreset.CLIMATE_PRESET_NONE, # Доступен всегда
    "ECO": ClimatePreset.CLIMATE_PRESET_ECO,
    "SLEEP": ClimatePreset.CLIMATE_PRESET_SLEEP,
    "COMFORT": ClimatePreset.CLIMATE_PRESET_COMFORT,
}

VerticalSwingDirection = tclac_ns.enum("VerticalSwingDirection", True)
VERTICAL_SWING_DIRECTION_OPTIONS = {
    "UP_DOWN": VerticalSwingDirection.UPDOWN,
    "UPSIDE": VerticalSwingDirection.UPSIDE,
    "DOWNSIDE": VerticalSwingDirection.DOWNSIDE,
}

HorizontalSwingDirection = tclac_ns.enum("HorizontalSwingDirection", True)
HORIZONTAL_SWING_DIRECTION_OPTIONS = {
    "LEFT_RIGHT": HorizontalSwingDirection.LEFT_RIGHT,
    "LEFTSIDE": HorizontalSwingDirection.LEFTSIDE,
    "CENTER": HorizontalSwingDirection.CENTER,
    "RIGHTSIDE": HorizontalSwingDirection.RIGHTSIDE,
}

AirflowVerticalDirection = tclac_ns.enum("AirflowVerticalDirection", True)
AIRFLOW_VERTICAL_DIRECTION_OPTIONS = {
    "LAST": AirflowVerticalDirection.LAST,
    "MAX_UP": AirflowVerticalDirection.MAX_UP,
    "UP": AirflowVerticalDirection.UP,
    "CENTER": AirflowVerticalDirection.CENTER,
    "DOWN": AirflowVerticalDirection.DOWN,
    "MAX_DOWN": AirflowVerticalDirection.MAX_DOWN,
}

AirflowHorizontalDirection = tclac_ns.enum("AirflowHorizontalDirection", True)
AIRFLOW_HORIZONTAL_DIRECTION_OPTIONS = {
    "LAST": AirflowHorizontalDirection.LAST,
    "MAX_LEFT": AirflowHorizontalDirection.MAX_LEFT,
    "LEFT": AirflowHorizontalDirection.LEFT,
    "CENTER": AirflowHorizontalDirection.CENTER,
    "RIGHT": AirflowHorizontalDirection.RIGHT,
    "MAX_RIGHT": AirflowHorizontalDirection.MAX_RIGHT,
}

# Проверка конфигурации интерфейса и принятие значений по умолчанию
def validate_visual(config):
    if CONF_VISUAL in config:
        visual_config = config[CONF_VISUAL]
        if CONF_MIN_TEMPERATURE in visual_config:
            min_temp = visual_config[CONF_MIN_TEMPERATURE]
            if min_temp < TCLAC_MIN_TEMPERATURE:
                raise cv.Invalid(f"Указанная интерфейсная минимальная температура в {min_temp} ниже допустимой {TCLAC_MIN_TEMPERATURE} для кондиционера")
        else:
            config[CONF_VISUAL][CONF_MIN_TEMPERATURE] = TCLAC_MIN_TEMPERATURE
        if CONF_MAX_TEMPERATURE in visual_config:
            max_temp = visual_config[CONF_MAX_TEMPERATURE]
            if max_temp > TCLAC_MAX_TEMPERATURE:
                raise cv.Invalid(f"Указанная интерфейсная максимальная температура в {max_temp} выше допустимой {TCLAC_MAX_TEMPERATURE} для кондиционера")
        else:
            config[CONF_VISUAL][CONF_MAX_TEMPERATURE] = TCLAC_MAX_TEMPERATURE
        if CONF_TEMPERATURE_STEP in visual_config:
            temp_step = config[CONF_VISUAL][CONF_TEMPERATURE_STEP][CONF_TARGET_TEMPERATURE]
            if ((int)(temp_step * 2)) / 2 != temp_step:
                raise cv.Invalid(f"Указанный шаг температуры {temp_step} не корректен, должен быть кратен 1")
        else:
            config[CONF_VISUAL][CONF_TEMPERATURE_STEP] = {CONF_TARGET_TEMPERATURE: TCLAC_TARGET_TEMPERATURE_STEP,CONF_CURRENT_TEMPERATURE: TCLAC_CURRENT_TEMPERATURE_STEP,}
    else:
        config[CONF_VISUAL] = {CONF_MIN_TEMPERATURE: TCLAC_MIN_TEMPERATURE,CONF_MAX_TEMPERATURE: TCLAC_MAX_TEMPERATURE,CONF_TEMPERATURE_STEP: {CONF_TARGET_TEMPERATURE: TCLAC_TARGET_TEMPERATURE_STEP,CONF_CURRENT_TEMPERATURE: TCLAC_CURRENT_TEMPERATURE_STEP,},}
    return config

# Проверка конфигурации компонента и принятие значений по умолчанию
CONFIG_SCHEMA = cv.All(
    climate.climate_schema(tclacClimate)
    .extend(
        {
            cv.Optional(CONF_BEEPER, default=True): cv.boolean,
            cv.Optional(CONF_DISPLAY, default=True): cv.boolean,
            cv.Optional(CONF_RX_LED): pins.gpio_output_pin_schema,
            cv.Optional(CONF_TX_LED): pins.gpio_output_pin_schema,
            cv.Optional(CONF_FORCE_MODE, default=True): cv.boolean,
            cv.Optional(CONF_MODULE_DISPLAY, default=True): cv.boolean,
            cv.Optional(CONF_VERTICAL_AIRFLOW, default="CENTER"): cv.ensure_list(cv.enum(AIRFLOW_VERTICAL_DIRECTION_OPTIONS, upper=True)),
            cv.Optional(CONF_VERTICAL_SWING_MODE, default="UP_DOWN"): cv.ensure_list(cv.enum(VERTICAL_SWING_DIRECTION_OPTIONS, upper=True)),
            cv.Optional(CONF_HORIZONTAL_AIRFLOW, default="CENTER"): cv.ensure_list(cv.enum(AIRFLOW_HORIZONTAL_DIRECTION_OPTIONS, upper=True)),
            cv.Optional(CONF_HORIZONTAL_SWING_MODE, default="LEFT_RIGHT"): cv.ensure_list(cv.enum(HORIZONTAL_SWING_DIRECTION_OPTIONS, upper=True)),
            cv.Optional(CONF_SUPPORTED_PRESETS,default=["NONE","ECO","SLEEP","COMFORT",],): cv.ensure_list(cv.enum(SUPPORTED_CLIMATE_PRESETS_OPTIONS, upper=True)),
            cv.Optional(CONF_SUPPORTED_SWING_MODES,default=["OFF","VERTICAL","HORIZONTAL","BOTH",],): cv.ensure_list(cv.enum(SUPPORTED_SWING_MODES_OPTIONS, upper=True)),
            cv.Optional(CONF_SUPPORTED_MODES,default=["OFF","AUTO","COOL","HEAT","DRY","FAN_ONLY",],): cv.ensure_list(cv.enum(SUPPORTED_CLIMATE_MODES_OPTIONS, upper=True)),
            cv.Optional(CONF_SUPPORTED_FAN_MODES,default=["AUTO","QUIET","LOW","MIDDLE","MEDIUM","HIGH","FOCUS","DIFFUSE",],): cv.ensure_list(cv.enum(SUPPORTED_FAN_MODES_OPTIONS, upper=True)),
        }
    )
    .extend(uart.UART_DEVICE_SCHEMA)
    .extend(cv.COMPONENT_SCHEMA),
    validate_visual,
)

ForceOnAction = tclac_ns.class_("ForceOnAction", automation.Action)
ForceOffAction = tclac_ns.class_("ForceOffAction", automation.Action)
BeeperOnAction = tclac_ns.class_("BeeperOnAction", automation.Action)
BeeperOffAction = tclac_ns.class_("BeeperOffAction", automation.Action)
DisplayOnAction = tclac_ns.class_("DisplayOnAction", automation.Action)
DisplayOffAction = tclac_ns.class_("DisplayOffAction", automation.Action)
ModuleDisplayOnAction = tclac_ns.class_("ModuleDisplayOnAction", automation.Action)
VerticalAirflowAction = tclac_ns.class_("VerticalAirflowAction", automation.Action)
ModuleDisplayOffAction = tclac_ns.class_("ModuleDisplayOffAction", automation.Action)
HorizontalAirflowAction = tclac_ns.class_("HorizontalAirflowAction", automation.Action)
VerticalSwingDirectionAction = tclac_ns.class_("VerticalSwingDirectionAction", automation.Action)
HorizontalSwingDirectionAction = tclac_ns.class_("HorizontalSwingDirectionAction", automation.Action)

TCLAC_ACTION_BASE_SCHEMA = automation.maybe_simple_id({cv.GenerateID(CONF_ID): cv.use_id(tclacClimate),})

# Регистрация событий включения и отключения дисплея кондиционера
@automation.register_action(
    "climate.tclac.display_on", DisplayOnAction, cv.Schema
)
@automation.register_action(
    "climate.tclac.display_off", DisplayOffAction, cv.Schema
)
async def display_action_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    return var

# Регистрация событий включения и отключения пищалки кондиционера
@automation.register_action(
    "climate.tclac.beeper_on", BeeperOnAction, cv.Schema
)
@automation.register_action(
    "climate.tclac.beeper_off", BeeperOffAction, cv.Schema
)
async def beeper_action_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    return var

# Регистрация событий включения и отключения светодиодов связи модуля
@automation.register_action(
    "climate.tclac.module_display_on", ModuleDisplayOnAction, cv.Schema
)
@automation.register_action(
    "climate.tclac.module_display_off", ModuleDisplayOffAction, cv.Schema
)
async def module_display_action_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    return var
    
# Регистрация событий включения и отключения принудительного применения настроек
@automation.register_action(
    "climate.tclac.force_mode_on", ForceOnAction, cv.Schema
)
@automation.register_action(
    "climate.tclac.force_mode_off", ForceOffAction, cv.Schema
)
async def force_mode_action_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    return var

# Регистрация события установки вертикальной фиксации заслонки
@automation.register_action(
    "climate.tclac.set_vertical_airflow",
    VerticalAirflowAction,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(tclacClimate),
            cv.Required(CONF_VERTICAL_AIRFLOW): cv.templatable(cv.enum(AIRFLOW_VERTICAL_DIRECTION_OPTIONS, upper=True)),
        }
    ),
)
async def tclac_set_vertical_airflow_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    template_ = await cg.templatable(
        config[CONF_VERTICAL_AIRFLOW], args, AirflowVerticalDirection
    )
    cg.add(var.set_direction(template_))
    return var


# Регистрация события установки горизонтальной фиксации заслонок
@automation.register_action(
    "climate.tclac.set_horizontal_airflow",
    HorizontalAirflowAction,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(tclacClimate),
            cv.Required(CONF_HORIZONTAL_AIRFLOW): cv.templatable(cv.enum(AIRFLOW_HORIZONTAL_DIRECTION_OPTIONS, upper=True)),
        }
    ),
)
async def tclac_set_horizontal_airflow_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    template_ = await cg.templatable(config[CONF_HORIZONTAL_AIRFLOW], args, AirflowHorizontalDirection)
    cg.add(var.set_direction(template_))
    return var


# Регистрация события установки вертикального качания шторки
@automation.register_action(
    "climate.tclac.set_vertical_swing_direction",
    VerticalSwingDirectionAction,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(tclacClimate),
            cv.Required(CONF_VERTICAL_SWING_MODE): cv.templatable(cv.enum(VERTICAL_SWING_DIRECTION_OPTIONS, upper=True)),
        }
    ),
)
async def tclac_set_vertical_swing_direction_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    template_ = await cg.templatable(config[CONF_VERTICAL_SWING_MODE], args, VerticalSwingDirection)
    cg.add(var.set_swing_direction(template_))
    return var


# Регистрация события установки горизонтального качания шторок
@automation.register_action(
    "climate.tclac.set_horizontal_swing_direction",
    HorizontalSwingDirectionAction,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(tclacClimate),
            cv.Required(CONF_HORIZONTAL_SWING_MODE): cv.templatable(cv.enum(HORIZONTAL_SWING_DIRECTION_OPTIONS, upper=True)),
        }
    ),
)
async def tclac_set_horizontal_swing_direction_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    template_ = await cg.templatable(config[CONF_HORIZONTAL_SWING_MODE], args, HorizontalSwingDirection)
    cg.add(var.set_swing_direction(template_))
    return var


# Добавление конфигурации в код
def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    yield cg.register_component(var, config)
    yield uart.register_uart_device(var, config)
    yield climate.register_climate(var, config)

    if CONF_BEEPER in config:
        cg.add(var.set_beeper_state(config[CONF_BEEPER]))
    if CONF_DISPLAY in config:
        cg.add(var.set_display_state(config[CONF_DISPLAY]))
    if CONF_FORCE_MODE in config:
        cg.add(var.set_force_mode_state(config[CONF_FORCE_MODE]))
    if CONF_SUPPORTED_MODES in config:
        cg.add(var.set_supported_modes(config[CONF_SUPPORTED_MODES]))
    if CONF_SUPPORTED_PRESETS in config:
        cg.add(var.set_supported_presets(config[CONF_SUPPORTED_PRESETS]))
    if CONF_MODULE_DISPLAY in config:
        cg.add(var.set_module_display_state(config[CONF_MODULE_DISPLAY]))
    if CONF_SUPPORTED_FAN_MODES in config:
        cg.add(var.set_supported_fan_modes(config[CONF_SUPPORTED_FAN_MODES]))
    if CONF_SUPPORTED_SWING_MODES in config:
        cg.add(var.set_supported_swing_modes(config[CONF_SUPPORTED_SWING_MODES]))

    if CONF_TX_LED in config:
        cg.add_define("CONF_TX_LED")
        tx_led_pin = yield cg.gpio_pin_expression(config[CONF_TX_LED])
        cg.add(var.set_tx_led_pin(tx_led_pin))
    if CONF_RX_LED in config:
        cg.add_define("CONF_RX_LED")
        rx_led_pin = yield cg.gpio_pin_expression(config[CONF_RX_LED])
        cg.add(var.set_rx_led_pin(rx_led_pin))