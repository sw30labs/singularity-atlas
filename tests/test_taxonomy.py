"""Taxonomy: keyword classification, gazetteer extraction, geo lookup."""

from __future__ import annotations

from singularity_atlas import taxonomy


class TestClassifyText:
    def test_compute_text_scores_compute(self):
        text = "NVIDIA unveils new GPU datacenter with gigawatt power draw and HBM memory"
        scores = taxonomy.classify_text(text)
        assert "compute" in scores
        assert scores["compute"] >= 3

    def test_multi_vector_text(self):
        text = "OpenAI raises $10 billion for humanoid robot datacenters"
        scores = taxonomy.classify_text(text)
        assert "capital" in scores
        assert "embodiment" in scores
        assert "compute" in scores

    def test_empty_and_irrelevant(self):
        assert taxonomy.classify_text("") == {}
        assert taxonomy.classify_text("a lovely day for a walk") == {}

    def test_word_boundary_no_false_positive(self):
        # "agi" must not match inside "imagination"
        scores = taxonomy.classify_text("pure imagination and magic")
        assert "capability" not in scores

    def test_case_insensitive(self):
        assert "capability" in taxonomy.classify_text("AGI SUPERINTELLIGENCE benchmark")


class TestExtractEntities:
    def test_canonical_dedupe(self):
        ents = taxonomy.extract_entities("DeepMind researchers; Google DeepMind labs")
        names = [e["name"] for e in ents]
        assert names.count("Google DeepMind") == 1

    def test_types_assigned(self):
        ents = {e["name"]: e["type"] for e in taxonomy.extract_entities(
            "Sam Altman met Jensen Huang at NVIDIA in Taiwan")}
        assert ents["Sam Altman"] == "person"
        assert ents["Jensen Huang"] == "person"
        assert ents["NVIDIA"] == "org"
        assert ents["Taiwan"] == "place"

    def test_model_entities(self):
        ents = {e["name"] for e in taxonomy.extract_entities("Claude and GPT-5 walk into a benchmark")}
        assert "Claude" in ents

    def test_moonshot_hosts_canonical(self):
        ents = {e["name"] for e in taxonomy.extract_entities(
            "Peter H. Diamandis sat with Alexander Wissner-Gross and Salim Ismail")}
        assert "Peter Diamandis" in ents
        assert "Alex Wissner-Gross" in ents
        assert "Salim Ismail" in ents

    def test_no_entities(self):
        assert taxonomy.extract_entities("nothing notable here") == []

    def test_figure_out_is_not_figure_ai(self):
        names = {e["name"] for e in taxonomy.extract_entities(
            "I figure this will be easy once we figure out the hidden figure")}
        assert "Figure AI" not in names

    def test_figure_ai_still_matches(self):
        names = {e["name"] for e in taxonomy.extract_entities("Brett Adcock at Figure AI")}
        assert "Figure AI" in names
        assert "Brett Adcock" in names


class TestGeo:
    def test_extract_places_with_coords(self):
        places = taxonomy.extract_places("fab expansion in Hsinchu and Phoenix")
        by_name = {p["name"]: p for p in places}
        assert "Hsinchu" in by_name
        assert by_name["Hsinchu"]["lat"] > 0
        assert by_name["Phoenix"]["lon"] < 0

    def test_places_only_for_known_geo(self):
        # orgs must never leak into places
        places = taxonomy.extract_places("OpenAI and Anthropic")
        assert places == []


class TestScoringHelpers:
    def test_top_vectors_order(self):
        tv = taxonomy.top_vectors({"a": 1.0, "b": 5.0, "c": 3.0}, k=2)
        assert tv == [("b", 5.0), ("c", 3.0)]

    def test_salience_monotonic(self):
        low = taxonomy.salience("small story", {})
        high = taxonomy.salience(
            "OpenAI NVIDIA TSMC gigawatt datacenter frontier model benchmark",
            {"compute": 5.0, "capability": 4.0})
        assert high > low >= 0
