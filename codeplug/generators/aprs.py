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
        self.aprs_channel = None
        self.aprs_config = None

    def channels(self, seq):
        f = 144.800
        if self.aprs_channel is None:
            self.aprs_channel = AnalogChannel(
                internal_id=seq.next(),
                name="APRS",
                rx_freq=f,
                tx_freq=f,
                tx_power=TxPower.Max,
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
        return [self.aprs_channel]

    def aprs(self, seq):
        if self.aprs_channel is None:
            raise "Generate channels first"
        if self.aprs_config is None:
            self.aprs_config = AnalogAPRSConfig(
                internal_id=seq.next(),
                name="Analog APRS",
                channel_id=self.aprs_channel.internal_id,
                source=f"{self.source}-7",
                destination="APAT81-0",
                path=["WIDE1-1", "WIDE2-1"],
                period=60,
                icon="Runner",
                message=f"{self.source} testing",
            )
        return self.aprs_config


class DigitalAPRSGenerator:
    def __init__(self, *, aprs_contact):
        self.aprs_config = None
        self.aprs_contact = aprs_contact

    # NOTE: 04/01/2024 (jps): Doesn't really apply here.
    def channels(self, _):
        return []

    def aprs(self, seq):
        if self.aprs_config is None:
            self.aprs_config = DigitalAPRSConfig(
                internal_id=seq.next(),
                name="DMR APRS",
                period=180,
                contact_id=self.aprs_contact.internal_id,
            )
        return self.aprs_config
