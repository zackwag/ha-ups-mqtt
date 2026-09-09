import pytest

from nut2mqtt import (
    build_command_topic,
    build_discovery_topic,
    build_state_topic,
    first_value,
    make_entity_id,
    require_config,
    sanitize_slug,
    switch_state_from_status,
    switch_state_on_values,
    validate_config,
)


# --- require_config ---


class TestRequireConfig:
    def test_single_key(self):
        assert require_config({"mqtt": "val"}, "mqtt") == "val"

    def test_nested_keys(self):
        cfg = {"mqtt": {"broker": "localhost"}}
        assert require_config(cfg, "mqtt", "broker") == "localhost"

    def test_missing_key_raises(self):
        with pytest.raises(KeyError, match="mqtt.broker"):
            require_config({"mqtt": {}}, "mqtt", "broker")

    def test_missing_top_level_raises(self):
        with pytest.raises(KeyError, match="mqtt"):
            require_config({}, "mqtt")

    def test_empty_value_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            require_config({"mqtt": {"broker": ""}}, "mqtt", "broker")

    def test_none_value_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            require_config({"key": None}, "key")

    def test_non_dict_intermediate_raises(self):
        with pytest.raises(KeyError):
            require_config({"mqtt": "string"}, "mqtt", "broker")


# --- validate_config ---


MINIMAL_CONFIG = {
    "mqtt": {"broker": "mqtt.local", "username": "u", "password": "p"},
    "ups": {"name": "ups1", "friendly_name": "My UPS"},
    "sensors": [{"key": "battery.charge", "friendly_name": "Battery"}],
}


class TestValidateConfig:
    def test_minimal_valid(self):
        result = validate_config(MINIMAL_CONFIG)
        assert result is MINIMAL_CONFIG

    def test_missing_mqtt_broker(self):
        cfg = {**MINIMAL_CONFIG, "mqtt": {"username": "u", "password": "p"}}
        with pytest.raises(KeyError, match="mqtt.broker"):
            validate_config(cfg)

    def test_missing_sensors(self):
        cfg = {**MINIMAL_CONFIG, "sensors": []}
        with pytest.raises(ValueError, match="No sensors"):
            validate_config(cfg)

    def test_commands_require_upscmd_credentials(self):
        cfg = {
            **MINIMAL_CONFIG,
            "commands": [{"key": "beeper.mute", "friendly_name": "Mute"}],
        }
        with pytest.raises(KeyError, match="upscmd_username"):
            validate_config(cfg)

    def test_commands_with_credentials(self):
        cfg = {
            **MINIMAL_CONFIG,
            "ups": {**MINIMAL_CONFIG["ups"], "upscmd_username": "u", "upscmd_password": "p"},
            "commands": [{"key": "beeper.mute", "friendly_name": "Mute"}],
        }
        assert validate_config(cfg) is cfg

    def test_switches_require_all_fields(self):
        cfg = {
            **MINIMAL_CONFIG,
            "ups": {**MINIMAL_CONFIG["ups"], "upscmd_username": "u", "upscmd_password": "p"},
            "switches": [{"key": "beeper", "friendly_name": "Beeper"}],
        }
        with pytest.raises(ValueError, match="missing required field"):
            validate_config(cfg)

    def test_switches_valid(self):
        cfg = {
            **MINIMAL_CONFIG,
            "ups": {**MINIMAL_CONFIG["ups"], "upscmd_username": "u", "upscmd_password": "p"},
            "switches": [{
                "key": "beeper",
                "friendly_name": "Beeper",
                "status_key": "ups.beeper.status",
                "command_on": "beeper.enable",
                "command_off": "beeper.disable",
            }],
        }
        assert validate_config(cfg) is cfg


# --- sanitize_slug ---


class TestSanitizeSlug:
    def test_simple(self):
        assert sanitize_slug("hello") == "hello"

    def test_uppercase(self):
        assert sanitize_slug("My UPS") == "my_ups"

    def test_special_chars(self):
        assert sanitize_slug("ups-1.local") == "ups_1_local"

    def test_leading_trailing_spaces(self):
        assert sanitize_slug("  test  ") == "test"

    def test_preserves_underscores(self):
        assert sanitize_slug("battery_charge") == "battery_charge"


# --- first_value ---


class TestFirstValue:
    def test_returns_first_found(self):
        data = {"a": 1, "b": 2}
        assert first_value(data, "a", "b") == 1

    def test_skips_missing(self):
        data = {"b": 2}
        assert first_value(data, "a", "b") == 2

    def test_returns_default_when_all_missing(self):
        assert first_value({}, "a", "b", default="fallback") == "fallback"

    def test_default_is_none(self):
        assert first_value({}, "a") is None

    def test_returns_falsy_value(self):
        assert first_value({"a": 0}, "a") == 0

    def test_skips_none_values(self):
        data = {"a": None, "b": "real"}
        assert first_value(data, "a", "b") == "real"


# --- topic builders ---


class TestTopicBuilders:
    def test_discovery_topic_default(self):
        assert build_discovery_topic("my_sensor") == "homeassistant/sensor/my_sensor/config"

    def test_discovery_topic_binary(self):
        assert build_discovery_topic("my_bin", "binary_sensor") == "homeassistant/binary_sensor/my_bin/config"

    def test_discovery_topic_button(self):
        assert build_discovery_topic("my_btn", "button") == "homeassistant/button/my_btn/config"

    def test_state_topic(self):
        assert build_state_topic("nut2mqtt", "ups_battery") == "nut2mqtt/ups_battery/state"

    def test_command_topic(self):
        assert build_command_topic("nut2mqtt", "ups_beeper") == "nut2mqtt/ups_beeper/set"


# --- make_entity_id ---


class TestMakeEntityId:
    def test_basic(self):
        assert make_entity_id("My UPS", "battery.charge") == "my_ups_battery_charge"

    def test_deduplicates_prefix(self):
        assert make_entity_id("My UPS", "my_ups_battery") == "my_ups_battery"

    def test_special_chars(self):
        assert make_entity_id("UPS-1", "ups.status") == "ups_1_ups_status"


# --- switch_state_on_values ---


class TestSwitchStateOnValues:
    def test_default(self):
        assert switch_state_on_values({}) == {"enabled"}

    def test_custom_list(self):
        assert switch_state_on_values({"state_on": ["enabled", "muted"]}) == {"enabled", "muted"}

    def test_string_value(self):
        assert switch_state_on_values({"state_on": "on"}) == {"on"}

    def test_lowercased(self):
        assert switch_state_on_values({"state_on": ["ENABLED"]}) == {"enabled"}


# --- switch_state_from_status ---


class TestSwitchStateFromStatus:
    def test_on(self):
        assert switch_state_from_status("enabled", {"enabled"}) == "ON"

    def test_off(self):
        assert switch_state_from_status("disabled", {"enabled"}) == "OFF"

    def test_case_insensitive(self):
        assert switch_state_from_status("ENABLED", {"enabled"}) == "ON"

    def test_strips_whitespace(self):
        assert switch_state_from_status("  enabled  ", {"enabled"}) == "ON"

    def test_muted_counts_as_on(self):
        assert switch_state_from_status("muted", {"enabled", "muted"}) == "ON"
