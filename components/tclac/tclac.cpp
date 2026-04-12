/**
* Create by Miguel Ángel López on 20/07/19
* and modify by xaxexa
* Refactoring & component making:
* Соловей с паяльником 15.03.2024
**/
#include "esphome.h"
#include "esphome/core/defines.h"
#include "tclac.h"

namespace esphome{
namespace tclac{


ClimateTraits tclacClimate::traits() {
	auto traits = climate::ClimateTraits();

	//traits.set_supports_action(false);
	//traits.set_supports_current_temperature(true);
	//traits.set_supports_two_point_target_temperature(false);

	traits.add_feature_flags(climate::CLIMATE_SUPPORTS_CURRENT_TEMPERATURE); // Предудущие методы запрещены, теперь нужно использовать add_feature_flags

	traits.set_supported_modes(this->supported_modes_);
	traits.set_supported_presets(this->supported_presets_);
	traits.set_supported_fan_modes(this->supported_fan_modes_);
	traits.set_supported_swing_modes(this->supported_swing_modes_);

	traits.add_supported_mode(climate::CLIMATE_MODE_OFF);			// Выключенный режим кондиционера доступен всегда
	traits.add_supported_mode(climate::CLIMATE_MODE_AUTO);			// Автоматический режим кондиционера тоже
	traits.add_supported_fan_mode(climate::CLIMATE_FAN_AUTO);		// Автоматический режим вентилятора доступен всегда
	traits.add_supported_swing_mode(climate::CLIMATE_SWING_OFF);	// Выключенный режим качания заслонок доступен всегда
	traits.add_supported_preset(ClimatePreset::CLIMATE_PRESET_NONE);// На всякий случай без предустановок

	return traits;
}


void tclacClimate::setup() {

#ifdef CONF_RX_LED
	this->rx_led_pin_->setup();
	this->rx_led_pin_->digital_write(false);
#endif
#ifdef CONF_TX_LED
	this->tx_led_pin_->setup();
	this->tx_led_pin_->digital_write(false);
#endif
}

void tclacClimate::loop()  {
    if (esphome::uart::UARTDevice::available() >= 5) { // Ждем минимум заголовок
        dataRX[0] = esphome::uart::UARTDevice::read();
        if (dataRX[0] != 0xBB) return;

        // Читаем остальные 4 байта заголовка без delay
        esphome::uart::UARTDevice::read_array(dataRX + 1, 4);

        // Читаем тело пакета. Длина в dataRX[4]
        uint8_t data_len = dataRX[4];
        esphome::uart::UARTDevice::read_array(dataRX + 5, data_len + 1);

        // Проверка CRC (использует XOR для длинных пакетов)
        byte check = getChecksum(dataRX, 61);
        if (check != dataRX[60]) {
            ESP_LOGV("TCL", "CRC Status Error"); // Используем LOGV чтобы не спамить
            return;
        }

        this->readData();
    }
}

void tclacClimate::update() {
	tclacClimate::dataShow(1,1);
	this->esphome::uart::UARTDevice::write_array(poll, sizeof(poll));
	//auto raw = tclacClimate::getHex(poll, sizeof(poll));
	//ESP_LOGD("TCL", "chek status sended");
	tclacClimate::dataShow(1,0);
}

void tclacClimate::readData() {
	current_temperature = float((( (dataRX[17] << 8) | dataRX[18] ) / 374 - 32)/1.8);
	target_temperature = (dataRX[FAN_SPEED_POS] & SET_TEMP_MASK) + 16;

	//ESP_LOGD("TCL", "TEMP: %f ", current_temperature);

	if (dataRX[MODE_POS] & ( 1 << 4)) {
		// Если кондиционер включен, то разбираем данные для отображения
		// ESP_LOGD("TCL", "AC is on");
		uint8_t modeswitch = MODE_MASK & dataRX[MODE_POS];
		uint8_t fanspeedswitch = FAN_SPEED_MASK & dataRX[FAN_SPEED_POS];
		uint8_t swingmodeswitch = SWING_MODE_MASK & dataRX[SWING_POS];

		switch (modeswitch) {
			case MODE_AUTO:
				mode = climate::CLIMATE_MODE_AUTO;
				break;
			case MODE_COOL:
				mode = climate::CLIMATE_MODE_COOL;
				break;
			case MODE_DRY:
				mode = climate::CLIMATE_MODE_DRY;
				break;
			case MODE_FAN_ONLY:
				mode = climate::CLIMATE_MODE_FAN_ONLY;
				break;
			case MODE_HEAT:
				mode = climate::CLIMATE_MODE_HEAT;
				break;
			default:
				mode = climate::CLIMATE_MODE_AUTO;
		}

		if ( dataRX[FAN_QUIET_POS] & FAN_QUIET) {
			fan_mode = climate::CLIMATE_FAN_QUIET;
		} else if (dataRX[MODE_POS] & FAN_DIFFUSE){
			fan_mode = climate::CLIMATE_FAN_DIFFUSE;
		} else {
			switch (fanspeedswitch) {
				case FAN_AUTO:
					fan_mode = climate::CLIMATE_FAN_AUTO;
					break;
				case FAN_LOW:
					fan_mode = climate::CLIMATE_FAN_LOW;
					break;
				case FAN_MIDDLE:
					fan_mode = climate::CLIMATE_FAN_MIDDLE;
					break;
				case FAN_MEDIUM:
					fan_mode = climate::CLIMATE_FAN_MEDIUM;
					break;
				case FAN_HIGH:
					fan_mode = climate::CLIMATE_FAN_HIGH;
					break;
				case FAN_FOCUS:
					fan_mode = climate::CLIMATE_FAN_FOCUS;
					break;
				default:
					fan_mode = climate::CLIMATE_FAN_AUTO;
			}
		}

		switch (swingmodeswitch) {
			case SWING_OFF:
				swing_mode = climate::CLIMATE_SWING_OFF;
				break;
			case SWING_HORIZONTAL:
				swing_mode = climate::CLIMATE_SWING_HORIZONTAL;
				break;
			case SWING_VERTICAL:
				swing_mode = climate::CLIMATE_SWING_VERTICAL;
				break;
			case SWING_BOTH:
				swing_mode = climate::CLIMATE_SWING_BOTH;
				break;
		}

		// Обработка данных о пресете
		preset = ClimatePreset::CLIMATE_PRESET_NONE;
		if (dataRX[7] & (1 << 6)){
			preset = ClimatePreset::CLIMATE_PRESET_ECO;
		} else if (dataRX[9] & (1 << 2)){
			preset = ClimatePreset::CLIMATE_PRESET_COMFORT;
		} else if (dataRX[19] & (1 << 0)){
			preset = ClimatePreset::CLIMATE_PRESET_SLEEP;
		}

	} else {
		// Если кондиционер выключен, то все режимы показываются, как выключенные
		mode = climate::CLIMATE_MODE_OFF;
		//fan_mode = climate::CLIMATE_FAN_OFF;
		swing_mode = climate::CLIMATE_SWING_OFF;
		preset = ClimatePreset::CLIMATE_PRESET_NONE;
	}
	// Публикуем данные
	this->publish_state();
	allow_take_control = true;
   }

// Climate control
void tclacClimate::control(const climate::ClimateCall &call) {
    if (call.get_mode().has_value()) this->mode = *call.get_mode();
    if (call.get_target_temperature().has_value()) this->target_temperature = *call.get_target_temperature();
    if (call.get_fan_mode().has_value()) this->fan_mode = *call.get_fan_mode();
	if (call.get_swing_mode().has_value()) this->swing_mode = *call.get_swing_mode();

    this->takeControl();
}

void tclacClimate::takeControl() {
    uint8_t dataTX[38];
    memset(dataTX, 0, sizeof(dataTX));

    // Сброс ключевых байтов перед заполнением
    dataTX[7] = 0; dataTX[8] = 0; dataTX[9] = 0; dataTX[10] = 0;
    dataTX[11] = 0; dataTX[19] = 0; dataTX[32] = 0; dataTX[33] = 0;

    // 1. Расчет температуры (Инвертированный: 31 - TEMP)
    float target = this->target_temperature;
    if (std::isnan(target)) target = 24.0f;
    uint8_t target_set = 31 - (int)target;

    // 2. Пищалка и Дисплей (байт 7)
    if (this->beeper_status_) dataTX[7] |= 0b00100000;
    if (this->display_status_ && this->mode != climate::CLIMATE_MODE_OFF) dataTX[7] |= 0b01000000;

    // 3. Режимы работы (байт 7 и 8)
    switch (this->mode) {
        case climate::CLIMATE_MODE_OFF:
            break; // Остаются нули
        case climate::CLIMATE_MODE_AUTO:
            dataTX[7] |= 0b00000100; dataTX[8] = 0b00001000;
            break;
        case climate::CLIMATE_MODE_COOL:
            dataTX[7] |= 0b00000100; dataTX[8] = 0b00000011;
            break;
        case climate::CLIMATE_MODE_DRY:
            dataTX[7] |= 0b00000100; dataTX[8] = 0b00000010;
            break;
        case climate::CLIMATE_MODE_FAN_ONLY:
            dataTX[7] |= 0b00000100; dataTX[8] = 0b00000111;
            break;
        case climate::CLIMATE_MODE_HEAT:
            dataTX[7] |= 0b00000100; dataTX[8] = 0b00000001;
            break;
		default:
            break;
    }

	// 4. Настройка вентилятора (байты 8 и 10)
    dataTX[10] = 0;

    if (this->fan_mode.has_value()) {
        switch (*this->fan_mode) {
            case climate::CLIMATE_FAN_AUTO:
                dataTX[10] |= 0b00000000; // AUTO — это всё по нулям
                break;
            case climate::CLIMATE_FAN_LOW:
                dataTX[10] |= 0b00000001;
                break;
            case climate::CLIMATE_FAN_MIDDLE:
                dataTX[10] |= 0b00000110;
                break;
            case climate::CLIMATE_FAN_MEDIUM:
                dataTX[10] |= 0b00000011;
                break;
            case climate::CLIMATE_FAN_HIGH:
                dataTX[10] |= 0b00000111;
                break;
            case climate::CLIMATE_FAN_FOCUS:
                dataTX[10] |= 0b00000101;
                break;
            case climate::CLIMATE_FAN_QUIET:
                dataTX[8]  |= 0b10000000;
                break;
            case climate::CLIMATE_FAN_DIFFUSE:
                dataTX[8]  |= 0b01000000;
                break;
			default:
                break;
        }
    }

	// 5. Управление качанием заслонок
    switch (this->swing_mode) {
        case climate::CLIMATE_SWING_VERTICAL:   dataTX[10] |= 0b00111000; break;
        case climate::CLIMATE_SWING_HORIZONTAL: dataTX[11] |= 0b00001000; break;
        case climate::CLIMATE_SWING_BOTH:       dataTX[10] |= 0b00111000; dataTX[11] |= 0b00001000; break;
        default: break;
    }

    // 6. Направления и фиксация (Vertical)
    switch(this->vertical_swing_direction_) {
        case VerticalSwingDirection::UP_DOWN:  dataTX[32] |= 0b00001000; break;
        case VerticalSwingDirection::UPSIDE:   dataTX[32] |= 0b00010000; break;
        case VerticalSwingDirection::DOWNSIDE: dataTX[32] |= 0b00011000; break;
        default: break;
    }
    switch(this->vertical_direction_) {
        case AirflowVerticalDirection::MAX_UP:   dataTX[32] |= 0b00000001; break;
        case AirflowVerticalDirection::UP:       dataTX[32] |= 0b00000010; break;
        case AirflowVerticalDirection::CENTER:   dataTX[32] |= 0b00000011; break;
        case AirflowVerticalDirection::DOWN:     dataTX[32] |= 0b00000100; break;
        case AirflowVerticalDirection::MAX_DOWN: dataTX[32] |= 0b00000101; break;
        default: break;
    }

    // 7. Направления и фиксация (Horizontal)
    switch(this->horizontal_swing_direction_) {
        case HorizontalSwingDirection::LEFT_RIGHT: dataTX[33] |= 0b00001000; break;
        case HorizontalSwingDirection::LEFTSIDE:   dataTX[33] |= 0b00010000; break;
        case HorizontalSwingDirection::CENTER:     dataTX[33] |= 0b00011000; break;
        case HorizontalSwingDirection::RIGHTSIDE:  dataTX[33] |= 0b00100000; break;
        default: break;
    }
    switch(this->horizontal_direction_) {
        case AirflowHorizontalDirection::MAX_LEFT:  dataTX[33] |= 0b00000001; break;
        case AirflowHorizontalDirection::LEFT:      dataTX[33] |= 0b00000010; break;
        case AirflowHorizontalDirection::CENTER:    dataTX[33] |= 0b00000011; break;
        case AirflowHorizontalDirection::RIGHT:     dataTX[33] |= 0b00000100; break;
        case AirflowHorizontalDirection::MAX_RIGHT: dataTX[33] |= 0b00000101; break;
        default: break;
    }

    // 8. Пресеты
    if (this->preset.has_value()) {
        switch (*this->preset) {
            case climate::CLIMATE_PRESET_ECO:    dataTX[7]  |= 0b10000000; break;
            case climate::CLIMATE_PRESET_SLEEP:  dataTX[19] |= 0b00000001; break;
            case climate::CLIMATE_PRESET_COMFORT:dataTX[8]  |= 0b00010000; break;
            default: break;
        }
    }

    // 9. Заполнение посылки
    dataTX[0] = 0xBB;
    dataTX[1] = 0x00;
    dataTX[2] = 0x01;
    dataTX[3] = 0x03;
    dataTX[4] = 0x20;
    dataTX[5] = 0x03;
    dataTX[6] = 0x01;
    dataTX[9] = target_set;
    dataTX[13] = 0x01;

    // 10. Контрольная сумма XOR (байт 37)
    uint8_t crc = 0;
    for (int i = 0; i < 37; i++) {
        crc ^= dataTX[i];
    }
    dataTX[37] = crc;

    // 11. Отправка
    this->esphome::uart::UARTDevice::write_array(dataTX, 38);
    this->flush();

    ESP_LOGD("TCL", "Sent Control: Mode=%d, Temp_Raw=%d, CRC=%02X",
             (int)this->mode, target_set, dataTX[37]);
}

// Отправка данных в кондиционер
void tclacClimate::sendData(byte * message, byte size) {
	tclacClimate::dataShow(1,1);
	//Serial.write(message, size);
	this->esphome::uart::UARTDevice::write_array(message, size);
	//auto raw = getHex(message, size);
	ESP_LOGD("TCL", "Message to TCL sended...");
	tclacClimate::dataShow(1,0);
}

// Преобразование байта в читабельный формат
String tclacClimate::getHex(byte *message, byte size) {
	String raw;
	for (int i = 0; i < size; i++) {
		raw += "\n" + String(message[i]);
	}
	raw.toUpperCase();
	return raw;
}

// Вычисление контрольной суммы
byte tclacClimate::getChecksum(const byte * message, size_t size) {
    byte position = size - 1;
    byte crc = 0;
    if (size > 40) {
        // Ответы
        for (int i = 0; i < position; i++) crc ^= message[i];
    } else {
        // Команды
        for (int i = 0; i < position; i++) crc += message[i];
    }
    return crc;
}

// Мигаем светодиодами
void tclacClimate::dataShow(bool flow, bool shine) {
	if (module_display_status_){
		if (flow == 0){
			if (shine == 1){
#ifdef CONF_RX_LED
				this->rx_led_pin_->digital_write(true);
#endif
			} else {
#ifdef CONF_RX_LED
				this->rx_led_pin_->digital_write(false);
#endif
			}
		}
		if (flow == 1) {
			if (shine == 1){
#ifdef CONF_TX_LED
				this->tx_led_pin_->digital_write(true);
#endif
			} else {
#ifdef CONF_TX_LED
				this->tx_led_pin_->digital_write(false);
#endif
			}
		}
	}
}

// Действия с данными из конфига

// Получение состояния пищалки
void tclacClimate::set_beeper_state(bool state) {
	this->beeper_status_ = state;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение состояния дисплея кондиционера
void tclacClimate::set_display_state(bool state) {
	this->display_status_ = state;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение состояния режима принудительного применения настроек
void tclacClimate::set_force_mode_state(bool state) {
	this->force_mode_status_ = state;
}
// Получение пина светодиода приема данных
#ifdef CONF_RX_LED
void tclacClimate::set_rx_led_pin(GPIOPin *rx_led_pin) {
	this->rx_led_pin_ = rx_led_pin;
}
#endif
// Получение пина светодиода передачи данных
#ifdef CONF_TX_LED
void tclacClimate::set_tx_led_pin(GPIOPin *tx_led_pin) {
	this->tx_led_pin_ = tx_led_pin;
}
#endif
// Получение состояния светодиодов связи модуля
void tclacClimate::set_module_display_state(bool state) {
	this->module_display_status_ = state;
}
// Получение режима фиксации вертикальной заслонки
void tclacClimate::set_vertical_airflow(AirflowVerticalDirection direction) {
	this->vertical_direction_ = direction;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение режима фиксации горизонтальных заслонок
void tclacClimate::set_horizontal_airflow(AirflowHorizontalDirection direction) {
	this->horizontal_direction_ = direction;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение режима качания вертикальной заслонки
void tclacClimate::set_vertical_swing_direction(VerticalSwingDirection direction) {
	this->vertical_swing_direction_ = direction;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение доступных режимов работы кондиционера
void tclacClimate::set_supported_modes(climate::ClimateModeMask modes) {
	this->supported_modes_ = modes;
}
// Получение режима качания горизонтальных заслонок
void tclacClimate::set_horizontal_swing_direction(HorizontalSwingDirection direction) {
	horizontal_swing_direction_ = direction;
	if (force_mode_status_){
		if (allow_take_control){
			tclacClimate::takeControl();
		}
	}
}
// Получение доступных скоростей вентилятора
void tclacClimate::set_supported_fan_modes(climate::ClimateFanModeMask modes){
	this->supported_fan_modes_ = modes;
}
// Получение доступных режимов качания заслонок
void tclacClimate::set_supported_swing_modes(climate::ClimateSwingModeMask modes) {
	this->supported_swing_modes_ = modes;
}
// Получение доступных предустановок
void tclacClimate::set_supported_presets(climate::ClimatePresetMask presets) {
  this->supported_presets_ = presets;
}


}
}
