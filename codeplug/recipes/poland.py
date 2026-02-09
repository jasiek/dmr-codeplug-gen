from . import BaseRecipe

from generators import Sequence
from generators.analogchan import (
    AnalogPMR446ChannelGenerator,
    AnalogChannelGeneratorFromPrzemienniki,
)
from generators.contacts import (
    BrandmeisterTGContactGenerator,
    BrandmeisterSpecialContactGenerator,
)
from generators.digitalchan import (
    DigitalChannelGeneratorFromBrandmeister,
    HotspotDigitalChannelGenerator,
)
from generators.grouplists import CountryGroupListGenerator
from generators.roaming import (
    RoamingChannelGeneratorFromBrandmeister,
    RoamingZoneFromCallsignGenerator,
)
from generators.scanlists import (
    CallsignPrefixAnalogScanListGenerator,
    CallsignPrefixDigitalScanListGenerator,
)
from generators.zones import (
    ZoneFromCallsignGenerator2,
    HotspotZoneGenerator,
    PMRZoneGenerator,
    AnalogZoneGenerator,
)
from aggregators import ChannelAggregator, ZoneAggregator, ContactAggregator
from callsign_matchers import RegexMatcher
from datasources.przemienniki import PrzemiennikiAPI


class Recipe(BaseRecipe):
    def __init__(
        self,
        callsign,
        dmr_id,
        filename,
        radio_class,
        writer_class,
        timezone=None,
        debug=False,
    ):
        super().__init__(
            callsign,
            dmr_id,
            filename,
            radio_class,
            writer_class,
            timezone,
            debug,
            aprs_region="EU",  # Poland uses EU APRS frequency
        )

    def prepare_contacts(self):
        """Prepare DMR contacts including Brandmeister TGs and special contacts."""
        # Get APRS contact generator from BaseRecipe
        aprs_contact_gen = self.prepare_aprs_contacts()

        self.brandmeister_contact_gen = BrandmeisterTGContactGenerator()
        self.bm_special_gen = BrandmeisterSpecialContactGenerator()

        self.contacts = ContactAggregator(
            aprs_contact_gen,
            self.bm_special_gen,
            self.brandmeister_contact_gen,
        ).contacts(self.contact_seq)

    def prepare_digital_channels(self):
        """Prepare digital (DMR) channels from Brandmeister and hotspot."""
        polish_tgs = self.brandmeister_contact_gen.matched_contacts("^260")
        uk_tgs = self.brandmeister_contact_gen.matched_contacts("^235")

        self.digital_channels = ChannelAggregator(
            HotspotDigitalChannelGenerator(
                polish_tgs + uk_tgs,
                aprs_config=self.digital_aprs_config,
                default_contact_id=self.bm_special_gen.parrot().internal_id,
            ),
            DigitalChannelGeneratorFromBrandmeister(
                "High",
                talkgroups=polish_tgs,
                aprs_config=self.digital_aprs_config,
                default_contact_id=self.bm_special_gen.parrot().internal_id,
                callsign_matcher=RegexMatcher(r"^SR[0-9]"),
            ),
        ).channels(self.chan_seq)

    def prepare_analog_channels(self):
        """Prepare analog (FM) channels from Przemienniki and PMR446."""
        self.analog_pmr_chan_gen = AnalogPMR446ChannelGenerator(
            aprs=self.analog_aprs_config
        )

        self.analog_channels = ChannelAggregator(
            self.analog_aprs,
            self.analog_pmr_chan_gen,
            AnalogChannelGeneratorFromPrzemienniki(
                PrzemiennikiAPI().repeaters_2m(),
                "High",
                aprs=self.analog_aprs_config,
            ),
            AnalogChannelGeneratorFromPrzemienniki(
                PrzemiennikiAPI().repeaters_70cm(),
                "High",
                aprs=self.analog_aprs_config,
            ),
        ).channels(self.chan_seq)

    def prepare_zones(self):
        """Prepare channel zones organized by callsign and type."""
        self.zones = ZoneAggregator(
            HotspotZoneGenerator(self.digital_channels),
            ZoneFromCallsignGenerator2(self.digital_channels),
            PMRZoneGenerator(self.analog_pmr_chan_gen.channels(None)),
            AnalogZoneGenerator(self.analog_channels),
        ).zones(self.zone_seq)

    def prepare_roaming(self):
        """Prepare roaming channels and zones for Polish repeaters."""
        polish_tgs = self.brandmeister_contact_gen.matched_contacts("^260")
        self.roaming_channels = RoamingChannelGeneratorFromBrandmeister(
            polish_tgs
        ).channels(self.rch_seq)
        self.roaming_zones = RoamingZoneFromCallsignGenerator(
            self.roaming_channels
        ).zones(Sequence())

    def prepare_scanlists(self):
        """Prepare scan lists grouped by callsign prefix for analog and digital channels."""
        scanlist_seq = Sequence()
        analog_scanlist_gen = CallsignPrefixAnalogScanListGenerator(
            self.analog_channels
        )
        digital_scanlist_gen = CallsignPrefixDigitalScanListGenerator(
            self.digital_channels
        )

        analog_scanlists = analog_scanlist_gen.scanlists(scanlist_seq)
        digital_scanlists = digital_scanlist_gen.scanlists(scanlist_seq)
        self.scanlists = analog_scanlists + digital_scanlists

        scanlist_map = {
            scanlist.name: scanlist.internal_id for scanlist in self.scanlists
        }

        for channel in self.analog_channels:
            prefix = analog_scanlist_gen.callsign_prefix(channel._rpt_callsign)
            if not prefix:
                continue
            scanlist_name = f"{prefix} {analog_scanlist_gen.suffix}"
            if scanlist_name in scanlist_map:
                channel.scanlist_id = scanlist_map[scanlist_name]

        for channel in self.digital_channels:
            prefix = digital_scanlist_gen.callsign_prefix(channel._rpt_callsign)
            if not prefix:
                continue
            scanlist_name = f"{prefix} {digital_scanlist_gen.suffix}"
            if scanlist_name in scanlist_map:
                channel.scanlist_id = scanlist_map[scanlist_name]

    def prepare_grouplists(self):
        """Prepare talkgroup lists for Polish country code (260)."""
        self.grouplists = list(
            CountryGroupListGenerator(self.contacts, 260).grouplists(Sequence())
        )

        # Assign the Poland grouplist to all digital channels
        if self.grouplists:
            poland_grouplist_id = self.grouplists[0].internal_id
            for channel in self.digital_channels:
                channel.rx_grouplist_id = poland_grouplist_id
