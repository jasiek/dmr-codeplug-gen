from models import (
    AnalogChannel,
    TxPower,
    ChannelWidth,
    AnalogAdmitCriteria,
    AnalogAPRSConfig,
    DigitalAPRSConfig,
)


class AnalogAPRSGenerator:
    def __init__(self, callsign):
        self.source = callsign
        self.aprs_channels = []
        self._aprs_config_eu = None
        self._aprs_config_us = None

    def channels(self, seq):
        if len(self.aprs_channels) > 0:
            return self.aprs_channels
        self.aprs_channels.append(
            AnalogChannel(
                internal_id=seq.next(),
                name="APRS EU",
                rx_freq=144.800,
                tx_freq=144.800,
                tx_power=TxPower.High,
                scanlist_id=None,
                tot=None,
                squelch=1,
                rx_tone=None,
                tx_tone=None,
                rx_only=False,
                admit_crit=AnalogAdmitCriteria.Free.value,
                width=ChannelWidth.Narrow,
                aprs=None,
                _lat=None,
                _lng=None,
                _locator=None,
                _rpt_callsign=None,
                _qth=None,
            )
        )
        self.aprs_channels.append(
            AnalogChannel(
                internal_id=seq.next(),
                name="APRS US",
                rx_freq=144.390,
                tx_freq=144.390,
                tx_power=TxPower.High,
                scanlist_id=None,
                tot=None,
                squelch=1,
                rx_tone=None,
                tx_tone=None,
                rx_only=False,
                admit_crit=AnalogAdmitCriteria.Free.value,
                width=ChannelWidth.Narrow,
                aprs=None,
                _lat=None,
                _lng=None,
                _locator=None,
                _rpt_callsign=None,
                _qth=None,
            )
        )
        return self.aprs_channels

    def aprs_config_eu(self, seq):
        if self._aprs_config_eu is None:
            self._aprs_config_eu = AnalogAPRSConfig(
                internal_id=seq.next(),
                name="Analog APRS EU",
                channel_id=self.aprs_channels[0].internal_id,
                source=f"{self.source}-7",
                destination="APAT81-0",
                path=["WIDE1-1", "WIDE2-1"],
                period=60,
                icon="Runner",
                message=f"{self.source} testing",
            )
        return self._aprs_config_eu

    def aprs_config_us(self, seq):
        if self._aprs_config_us is None:
            self._aprs_config_us = AnalogAPRSConfig(
                internal_id=seq.next(),
                name="Analog APRS US",
                channel_id=self.aprs_channels[1].internal_id,
                source=f"{self.source}-7",
                destination="APAT81-0",
                path=["WIDE1-1", "WIDE2-1"],
                period=60,
                icon="Runner",
                message=f"{self.source} testing",
            )
        return self._aprs_config_us


class DigitalAPRSGenerator:
    def __init__(self, *, aprs_contact):
        self.aprs_config = None
        self.aprs_contact = aprs_contact

    # NOTE: 04/01/2024 (jps): Doesn't really apply here.
    def channels(self, _):
        return []

    def digital_aprs_config(self, seq):
        if self.aprs_config is None:
            self.aprs_config = DigitalAPRSConfig(
                internal_id=seq.next(),
                name="DMR APRS",
                period=180,
                contact_id=self.aprs_contact.internal_id,
            )
        return self.aprs_config
