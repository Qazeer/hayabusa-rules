from unittest import TestCase
from logsource_mapping import *


class TestLogSourceMapper(TestCase):
    def test_create_service_map(self):
        res = create_service_map(create_obj("windows-services.yaml"))
        self.assertEquals(len(res.keys()), 36)

    def test_create_category_map(self):
        service_to_channels = create_service_map(create_obj("windows-services.yaml"))
        s1 = create_category_map(create_obj('sysmon.yaml'), service_to_channels)
        s2 = create_category_map(create_obj('windows-audit.yaml'), service_to_channels)
        s3 = create_category_map(create_obj('windows-services.yaml'), service_to_channels)
        s4 = merge_category_map(service_to_channels, [s1, s2, s3])
        self.assertEquals(len(s4), 66)
        self.assertEquals(len(s4["process_creation"]), 2)

    def test_build_out_path(self):
        sigma_path = "/hoge/sigma/builtin/security/sample.yml"
        base_dir = "/hoge/sigma"
        out_dir = "/hoge/hayabusa_rule"
        sysmon = True
        r = build_out_path(base_dir, out_dir, sigma_path, sysmon)
        self.assertEquals(r, "/hoge/hayabusa_rule/sysmon/security/sample.yml")
        sysmon = False
        r = build_out_path(base_dir, out_dir, sigma_path, sysmon)
        self.assertEquals(r, "/hoge/hayabusa_rule/builtin/security/sample.yml")

    def test_get_key(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=1)
        self.assertEquals(ls.get_identifier_for_detection([]), "process_creation")

    def test_get_uniq_key(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=1)
        self.assertEquals(ls.get_identifier_for_detection(["process_creation"]), "logsource_mapping_process_creation")

    def test_get_detection(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=None)
        self.assertEquals(ls.get_detection(), {"Channel": "hoge"})

    def test_get_condition(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=None)
        self.assertEquals(ls.get_condition("select1 and select2", [], dict()),
                          "process_creation and (select1 and select2)")

    def test_get_single_condition(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=None)
        self.assertEquals(ls.get_condition("select", [], dict()), "process_creation and select")

    def test_get_aggregation_condition(self):
        ls = LogSource(category="process_creation", service="sysmon", channel="hoge", event_id=None)
        condition = "select | count(TargetUserName) by Workstation > 10"
        self.assertEquals(ls.get_condition(condition, [], dict()),
                          "(process_creation and select) | count(TargetUserName) by Workstation > 10")

    def test_get_aggregation_conversion_field_condition(self):
        ls = LogSource(category="process_creation", service="Security", channel="hoge", event_id=4688)
        condition = "select | count(Image) by Workstation > 10"
        self.assertEquals(ls.get_condition(condition, [], {"Image": "NewProcessName"}),
                          "(process_creation and select) | count(NewProcessName) by Workstation > 10")

    def test_get_logsources(self):
        service2channel = create_service_map(create_obj("windows-services.yaml"))
        sysmon_map = create_category_map(create_obj('sysmon.yaml'), service2channel)
        win_audit_map = create_category_map(create_obj('windows-audit.yaml'), service2channel)
        win_service_map = create_category_map(create_obj('windows-services.yaml'), service2channel)
        all_category_map = merge_category_map(service2channel, [sysmon_map, win_audit_map, win_service_map])
        process_creation_field_map = create_field_map(create_obj('windows-audit.yaml'))
        lc = LogsourceConverter("", all_category_map, process_creation_field_map, [])
        r = lc.get_logsources({"logsource": {"service": "sysmon"}})
        self.assertEquals(r[0].service, "sysmon")

    def test_get_logsources_raise_exception_if_not_supported_category(self):
        service2channel = create_service_map(create_obj("windows-services.yaml"))
        sysmon_map = create_category_map(create_obj('sysmon.yaml'), service2channel)
        win_audit_map = create_category_map(create_obj('windows-audit.yaml'), service2channel)
        win_service_map = create_category_map(create_obj('windows-services.yaml'), service2channel)
        all_category_map = merge_category_map(service2channel, [sysmon_map, win_audit_map, win_service_map])
        process_creation_field_map = create_field_map(create_obj('windows-audit.yaml'))
        lc = LogsourceConverter("", all_category_map, process_creation_field_map, [])
        with self.assertRaises(Exception):
            lc.get_logsources({"logsource": {"service": "file_rename"}})
