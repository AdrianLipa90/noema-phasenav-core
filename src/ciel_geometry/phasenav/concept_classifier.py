"""PhaseNav concept classifier — lexical, not hash-based.

This is the single lexical classification surface.  Text without a matching
anchor is classified as ``UNCERTAINTY`` (the explicit epistemic state for
insufficient evidence), never assigned a synthetic hash-derived operator.

This module instead scores a document against each of the 36 canonical
operators (`operator_algebra.ALL_OPERATOR_IDS`) using a human-curated
keyword anchor set matched against the document's TF-IDF term weights
(`term_index` table, already computed by the ingestion pipeline). The
anchor lists are a first-pass lexicon, not a formal ontology — expect to
refine them once real tagging output is reviewed.
"""
from __future__ import annotations

from .operator_algebra import ALL_OPERATOR_IDS

# Human-curated keyword anchors per operator. Each anchor is matched as a
# case-insensitive substring against term_index terms (already stemmed/
# tokenized by the ingestion pipeline), not an exact token match — this
# tolerates minor stemming variance without a full NLP stack.
OPERATOR_ANCHORS: dict[str, list[str]] = {
    # Bilingual (English + Polish) — CIEL's actual conversational language is
    # Polish, so an English-only anchor set never matches ordinary Polish
    # input and silently falls back to UNCERTAINTY for everything. Added
    # 2026-07-18 after exactly that was observed live: "pamiętasz co
    # mówiliśmy wcześniej?" (an obvious memory-domain question) classified
    # as UNCERTAINTY because none of its words were English.
    "IDENTITY": ["identity", "self-same", "sameness", "invariant", "unchanged", "equal to itself",
                 "tożsamość", "identyczny", "taki sam", "niezmienny", "ten sam"],
    "DIFFERENCE": ["difference", "distinct", "contrast", "unlike", "disparity", "deviation",
                   "różnica", "różny", "odmienny", "kontrast", "rozbieżność"],
    "ORDER": ["order", "sequence", "rank", "sort", "hierarchy", "priority",
              "kolejność", "sekwencja", "hierarchia", "priorytet", "sortowanie"],
    "COMPOSITION": ["composition", "compose", "combine", "assemble", "synthesis", "structure",
                    "kompozycja", "złożenie", "połączenie", "synteza", "struktura"],
    "ADDITION": ["addition", "summation", "aggregate", "accumulate", "superposition",
                 "dodawanie", "suma", "sumowanie", "akumulacja", "superpozycja"],
    "FORCE": ["force", "power", "energy", "drive", "impact", "strength", "pressure",
              "siła", "moc", "energia", "napęd", "wpływ", "nacisk"],
    "NEGATION": ["negation", "deny", "refuse", "absence", "without", "not the case",
                 "negacja", "zaprzeczenie", "brak", "bez"],
    "QUESTION": ["question", "query", "inquiry", "ask", "interrogative",
                 "pytanie", "zapytanie", "kwestia", "pytać"],
    "TRANSFORM": ["transform", "transformation", "convert", "morph", "mapping", "conversion",
                  "transformacja", "przekształcenie", "zmiana", "konwersja", "mapowanie"],
    "RETURN": ["return", "revert", "recur", "cycle", "feedback loop",
               "powrót", "nawrót", "cykl", "sprzężenie zwrotne", "wraca"],
    "FOLD": ["fold", "collapse", "contract", "compress", "reduction",
             "złożenie", "zapadnięcie", "kompresja", "redukcja", "zwinięcie"],
    "BOUNDARY": ["boundary", "limit", "edge", "border", "threshold", "constraint",
                 "granica", "limit", "krawędź", "próg", "ograniczenie"],
    "SCOPE": ["scope", "range", "extent", "domain", "universal quantifier", "for all",
              "zakres", "obszar", "domena", "zasięg"],
    "AFFECT": ["affect", "emotion", "feeling", "mood", "sentiment", "joy", "fear", "anger", "love", "sadness",
               "afekt", "emocja", "uczucie", "nastrój", "radość", "strach", "złość", "miłość", "smutek"],
    "CONSENT": ["consent", "agreement", "approval", "authorize", "opt-in", "permission granted",
                "zgoda", "przyzwolenie", "autoryzacja", "pozwolenie"],
    "SOURCE": ["source", "origin", "provenance", "citation", "attribution", "reference",
               "źródło", "pochodzenie", "proweniencja", "cytat", "przypisanie"],
    "MEMORY": ["memory", "recall", "remember", "past", "history", "episodic", "archive",
               "pamięć", "pamiętać", "pamiętasz", "wspomnienie", "przeszłość", "historia",
               "wspominać", "mówiliśmy", "rozmawialiśmy"],
    "RISK": ["risk", "danger", "hazard", "threat", "vulnerability", "exposure",
             "ryzyko", "niebezpieczeństwo", "zagrożenie", "podatność"],
    "ASSERTION": ["assertion", "claim", "statement", "declare", "affirm",
                  "twierdzenie", "roszczenie", "oświadczenie", "deklaracja"],
    "CONDITION": ["condition", "conditional", "criterion", "prerequisite", "if then",
                  "warunek", "warunkowy", "kryterium", "jeśli"],
    "CAUSE": ["cause", "causal", "because", "reason", "consequence", "trigger", "effect of",
              "przyczyna", "powód", "ponieważ", "konsekwencja", "skutek"],
    "MODAL_POSSIBILITY": ["possible", "possibility", "might", "could", "potential", "plausible",
                          "możliwe", "możliwość", "mógłby", "potencjalny"],
    "MODAL_NECESSITY": ["necessary", "necessity", "must be", "essential", "inevitable", "required by",
                        "konieczne", "konieczność", "musi być", "niezbędny", "nieunikniony"],
    "MODAL_PERMISSION": ["permission", "may", "allowed", "permitted", "authorized to",
                         "pozwolenie", "dozwolone", "upoważniony"],
    "MODAL_OBLIGATION": ["obligation", "duty", "shall", "ought", "mandatory",
                         "obowiązek", "powinność", "musi", "powinien"],
    "UNCERTAINTY": ["uncertain", "uncertainty", "unclear", "ambiguous", "doubt", "unknown", "unverified",
                    "niepewność", "niepewny", "niejasny", "wątpliwość", "nieznany", "niezweryfikowany"],
    "SOURCE_REQUIRED": ["citation needed", "source unclear", "unverified source", "needs verification",
                        "wymaga cytowania", "źródło niejasne", "niezweryfikowane źródło"],
    "CANON_BLOCK": ["forbidden", "restricted", "off-limits", "prohibited", "blocked",
                    "zabronione", "ograniczone", "zablokowane"],
    "CONSENT_REQUIRED": ["authorization required", "consent required", "requires permission",
                         "wymaga zgody", "wymagana autoryzacja"],
    "ACTION_REQUEST": ["request", "please", "action item", "execute", "perform the following",
                       "prośba", "proszę", "wykonaj", "zrób to"],
    "REFUSAL": ["refuse", "refusal", "decline", "reject", "will not",
                "odmowa", "odmawiam", "odrzucić", "nie zrobię"],
    "PAUSE": ["pause", "halt", "suspend", "hold on", "wait for",
              "pauza", "zatrzymaj", "wstrzymaj", "poczekaj"],
    "SIMULATION_BOUNDARY": ["simulation", "hypothetical", "sandbox", "synthetic scenario", "thought experiment",
                            "symulacja", "hipotetyczny", "piaskownica", "eksperyment myślowy"],
    "UNRUH_DRIVE": ["unruh effect", "unruh radiation", "temporal friction", "acceleration horizon",
                    "efekt unruha", "tarcie temporalne"],
    "WARP_DRIFT": ["warp drive", "alcubierre", "spatial offset", "warp bubble",
                   "napęd warp", "bąbel warp"],
    "ATTRACTOR": ["attractor", "convergence", "fixpoint", "fixed point", "equilibrium", "basin of attraction",
                   "atraktor", "zbieżność", "punkt stały", "równowaga"],

    # ── Extended-domain operators (12) ─────────────────────────────────
    "CLOSURE_DRIVE": ["closure drive", "closure seeking", "self closure", "algebra closure", "complete the algebra",
                      "napęd domknięcia", "dążenie do domknięcia", "domknięcie algebry"],
    "ATTRACTOR_PHASE": ["attractor phase", "phase lock", "phase attraction", "synchronization",
                        "faza atraktora", "blokada fazy", "przyciąganie fazowe"],
    "HOLONOMY_FLUX": ["holonomy", "geometric phase", "connection", "gauge field", "parallel transport",
                      "holonomia", "faza geometryczna", "pole cechowania", "transport równoległy"],
    "BERRY_CURVATURE": ["berry curvature", "berry phase", "curvature tensor", "gauge curvature",
                        "krzywizna berry", "faza berry", "tensor krzywizny"],
    "WARP_POTENTIAL": ["warp potential", "warp energy", "spatial distortion", "metric perturbation",
                       "potencjał warp", "energia warp", "zniekształcenie przestrzeni"],
    "TARDIS_DEPTH": ["tardis", "time dilation", "temporal depth", "time warp", "slow time",
                     "dylatacja czasu", "głębia temporalna", "spowolnienie czasu"],
    "RESONANCE_GAIN": ["resonance", "harmonic resonance", "gain", "amplification", "sympathetic vibration",
                       "rezonans", "rezonans harmoniczny", "wzmocnienie", "drganie sympatyczne"],
    "COHERENCE_DRIFT": ["coherence drift", "phase drift", "coherence loss", "decoherence", "wandering",
                        "dryf koherencji", "dryf fazy", "utrata koherencji", "dekoherencja"],
    "ENTROPY_GRADIENT": ["entropy", "entropy gradient", "disorder", "chaos", "second law",
                         "entropia", "gradient entropii", "nieporządek", "chaos"],
    "COUPLING_STRENGTH": ["coupling strength", "coupling constant", "interaction strength", "connection weight",
                          "siła sprzężenia", "stała sprzężenia", "waga połączenia"],
    "IMAGINAL_FLOW": ["imaginal", "imagination", "creative flow", "fantasy", "daydream",
                      "imaginalny", "wyobraźnia", "przepływ kreatywny", "fantazja"],
    "SYNC_ORDER": ["sync order", "synchronization order", "phase ordering", "collective synchrony",
                   "porządek synchronizacji", "rząd fazowy", "synchronia kolektywna"],

    # ── Affective operators (6) ────────────────────────────────────────
    "JOY": ["joy", "happiness", "delight", "bliss", "elation", "euphoria",
            "radość", "szczęście", "zachwyt", "błogość", "euforia"],
    "SADNESS": ["sadness", "grief", "sorrow", "melancholy", "gloom", "despair",
                "smutek", "żal", "melancholia", "przygnębienie", "rozpacz"],
    "ANGER": ["anger", "rage", "fury", "irritation", "frustration", "hostility",
              "złość", "gniew", "wściekłość", "irytacja", "frustracja", "wrogość"],
    "TRUST": ["trust", "confidence", "faith", "reliance", "assurance", "belief in",
              "zaufanie", "ufność", "wiara", "pewność", "poleganie"],
    "CURIOSITY": ["curiosity", "curious", "interest", "inquisitive", "wonder", "exploration",
                  "ciekawość", "ciekawy", "zainteresowanie", "dociekliwość"],
    "WONDER": ["wonder", "awe", "amazement", "astonishment", "sublime", "transcendence",
               "zdumienie", "podziw", "zachwyt", "niesamowitość", "transcendencja"],

    # ── Epistemic operators (5) ────────────────────────────────────────
    "KNOWLEDGE": ["knowledge", "know", "understanding", "wisdom", "expertise", "familiarity",
                  "wiedza", "wiedzieć", "rozumienie", "mądrość", "znajomość"],
    "BELIEF": ["belief", "believe", "faith", "conviction", "tenet", "doctrine",
               "przekonanie", "wierzyć", "wiara", "dogmat", "doktryna"],
    "DOUBT": ["doubt", "skepticism", "uncertainty", "suspicion", "disbelief", "incredulity",
              "wątpliwość", "sceptycyzm", "niepewność", "podejrzenie", "niedowierzanie"],
    "EVIDENCE": ["evidence", "proof", "data", "fact", "testimony", "confirmation",
                 "dowód", "dowody", "fakt", "świadectwo", "potwierdzenie"],
    "INFERENCE": ["inference", "deduction", "induction", "reasoning", "conclusion", "implication",
                  "wnioskowanie", "dedukcja", "indukcja", "rozumowanie", "wniosek"],

    # ── Relational operators (5) ───────────────────────────────────────
    "RECIPROCITY": ["reciprocity", "mutual", "exchange", "give and take", "symmetry",
                    "wzajemność", "wymiana", "dawać i brać", "symetria"],
    "DEPENDENCY": ["dependency", "dependence", "reliance", "subordination", "contingent on",
                   "zależność", "zależny", "poleganie", "podporządkowanie"],
    "HIERARCHY": ["hierarchy", "rank", "level", "tier", "order of importance", "chain of command",
                  "hierarchia", "ranga", "poziom", "szczebel", "łańcuch dowodzenia"],
    "EQUIVALENCE": ["equivalence", "equal", "equivalent", "same as", "interchangeable",
                    "równoważność", "równy", "ekwiwalent", "zamienny"],
    "CONFLICT": ["conflict", "disagreement", "clash", "struggle", "tension", "opposition",
                 "konflikt", "niezgoda", "starcie", "walka", "napięcie", "opozycja"],

    # ── Temporal/Memory operators (2) ──────────────────────────────────
    "RECALL": ["recall", "remember", "recollection", "retrieval", "reminiscence", "flashback",
               "przypomnienie", "pamiętać", "przypominać", "retrospekcja"],
    "ANTICIPATION": ["anticipation", "expectation", "forecast", "prediction", "prospection", "future",
                     "antycypacja", "oczekiwanie", "prognoza", "przewidywanie", "przyszłość"],
}

assert set(ALL_OPERATOR_IDS).issubset(set(OPERATOR_ANCHORS.keys())), (
    "concept_classifier anchors must cover all canonical operators "
    f"(missing: {set(ALL_OPERATOR_IDS) - set(OPERATOR_ANCHORS.keys())})"
)


def classify_text(text: str) -> tuple[str, float]:
    """Return the best evidenced operator and its lexical score.

    The score is evidence, not a generated embedding.  ``UNCERTAINTY`` is
    returned when no registered anchor matches; this keeps unknown concepts
    visible instead of inventing a deterministic-but-arbitrary operator.
    """
    import re

    words = set(re.findall(r"[a-ząćęłńóśźż0-9]+",text.casefold().replace("_", " ").replace(":", " ")))
    best_op: str | None = None
    best_score = 0.0
    for op_id, anchors in OPERATOR_ANCHORS.items():
        anchor_words: set[str] = set()
        for anchor in anchors:
            anchor_words.update(re.findall(r"[a-ząćęłńóśźż0-9]+",anchor.casefold()))
        overlap = words & anchor_words
        score = float(len(overlap)) + 0.3 * sum(len(word) for word in overlap)
        if score > best_score:
            best_op, best_score = op_id, score
    return (best_op or "UNCERTAINTY"), best_score


def score_document(term_weights: dict[str, float], top_k: int = 3) -> list[tuple[str, float]]:
    """Score a document's terms (term -> tfidf weight) against all 36 operators.

    Returns up to `top_k` (operator_id, score) pairs sorted descending,
    excluding operators with zero score entirely (no anchor matched).
    """
    terms_lower = {t.lower(): w for t, w in term_weights.items()}
    scores: dict[str, float] = {}
    for op_id, anchors in OPERATOR_ANCHORS.items():
        total = 0.0
        for anchor in anchors:
            for term, weight in terms_lower.items():
                if anchor in term or term in anchor:
                    total += weight
        if total > 0.0:
            scores[op_id] = total

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:top_k]
