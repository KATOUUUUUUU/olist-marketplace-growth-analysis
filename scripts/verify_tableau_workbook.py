"""Check portable package structure and embedded data; not a visual UI test."""
from collections import Counter
from pathlib import Path, PurePosixPath
import csv
import io
import json
import tempfile
from zipfile import ZipFile

from lxml import etree as ET
from tableauhyperapi import Connection, HyperProcess, Telemetry

ROOT = Path(__file__).resolve().parents[1]


def comparable(value):
    if value is None or value == "":
        return None
    text = str(value)
    try:
        return float(text)
    except ValueError:
        return text


def main():
    package = ROOT / "dashboard/olist_growth_dashboard.twbx"
    with ZipFile(package) as archive, tempfile.TemporaryDirectory(prefix="olist-package-check-") as temp:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate archive member"
        for name in names:
            path = PurePosixPath(name)
            assert not path.is_absolute() and ".." not in path.parts, name
        xml = archive.read("olist_growth_dashboard.twb")
        assert xml == (ROOT / "dashboard/olist_growth_dashboard.twb").read_bytes()
        tree = ET.fromstring(xml)
        assert b"/Users/" not in xml and b"/private/" not in xml, "Machine-specific path"
        pages = [d.get("name") for d in tree.findall("./dashboards/dashboard")]
        assert pages == ["Where Should Olist Grow Next?", "Growth & Customer Experience"]
        sources = {ds.get("name"): ds for ds in tree.findall("./datasources/datasource")}
        sheets = {s.get("name") for s in tree.findall("./worksheets/worksheet")}
        assert len(sheets) == 6
        month = tree.find('.//worksheet[@name="Monthly Delivered Orders and Product Value"]//column-instance[@column="[order_month]"]')
        assert month.get("derivation") == "Month-Trunc", "Do not merge the same month across years"
        assert month.get("name") == "[tmn:order_month:qk]"
        action = tree.find('./actions/action[@caption="Highlight State"]')
        assert action is not None
        assert action.find('activation').get('auto-clear') == 'true'
        assert action.find('.//param[@name="exclude"]').get('value') == 'KPI Overview'
        assert action.find('.//param[@name="field-captions"]').get('value') == 'State'
        for zone in tree.findall("./dashboards/dashboard/zones//zone[@name]"):
            assert zone.get("name") in sheets
        for ds in sources.values():
            for connection in ds.findall('.//connection[@class="hyper"]'):
                assert connection.get("dbname") in names
            for connection in ds.findall('.//connection[@class="textscan"]'):
                assert connection.get("directory") + "/" + connection.get("filename") in names
        for dep in tree.findall("./worksheets/worksheet/table/view/datasource-dependencies"):
            source = sources[dep.get("datasource")]
            fields = {c.get("name") for c in source.findall("column")}
            for instance in dep.findall("column-instance"):
                assert instance.get("column") in fields, instance.get("column")
        inputs = sorted((ROOT / "outputs/tableau").glob("*.csv"))
        assert len(inputs) == 5
        counts = {}
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={"log_dir": temp}) as hp:
            for file in inputs:
                member = "Data/" + file.name
                assert archive.read(member) == file.read_bytes(), file.name
                rows = list(csv.DictReader(io.StringIO(file.read_text())))
                hyper_member = str(PurePosixPath(member).with_suffix(".hyper"))
                hyper_path = Path(temp) / Path(hyper_member).name
                hyper_path.write_bytes(archive.read(hyper_member))
                with Connection(hp.endpoint, str(hyper_path)) as con:
                    actual = con.execute_list_query('SELECT * FROM "Extract"."Extract"')
                expected = Counter(tuple(comparable(v) for v in row.values()) for row in rows)
                observed = Counter(tuple(comparable(v) for v in row) for row in actual)
                assert expected == observed, file.name
                counts[file.name] = len(actual)
        report = {"status": "passed", "dashboard_pages": pages, "worksheet_count": len(sheets),
                  "embedded_sources": counts, "relative_paths_only": True,
                  "embedded_data_matches_csvs": True, "visual_test": "not performed by this script"}
        print(json.dumps(report, indent=2))
        return report


if __name__ == "__main__":
    main()
