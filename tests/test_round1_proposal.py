"""No NAS, official checker or external services used here."""
import copy,sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_round1_proposal import errors,word_count,render_markdown,JSON_PATH,MD_PATH
class Round1ProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(JSON_PATH.read_text(encoding="utf8"))
        cls.markdown=MD_PATH.read_text(encoding="utf8")
    def test_exact_official_ten_questions(self):
        self.assertEqual([],errors(self.data,self.markdown))
    def test_exact_official_rule_prompt_wording(self):
        self.assertTrue(self.data["questions"][0]["prompt"].startswith("One sentence:"))
        self.assertIn("expert agent orchestration",self.data["questions"][6]["prompt"])
        self.assertIn("technical risks",self.data["questions"][9]["prompt"])
    def test_true_351_answer_words(self):
        self.assertEqual(351,sum(word_count(q["answer"]) for q in self.data["questions"]))
    def test_more_than_500_rejected(self):
        d=copy.deepcopy(self.data);d["questions"][0]["answer"]="word "*510
        self.assertTrue(any("Word cap exceeded" in x for x in errors(d)))
    def test_status_must_remain_unsubmitted(self):
        d=copy.deepcopy(self.data);d["status"]="SUBMITTED"
        self.assertTrue(errors(d))
    def test_bad_question_order_rejected(self):
        d=copy.deepcopy(self.data);d["questions"][0]["prompt"]="unofficial"
        self.assertTrue(errors(d))
    def test_false_nas_validation_rejected(self):
        d=copy.deepcopy(self.data);d["proof_status"]["nas"]="PASS"
        self.assertTrue(errors(d))
    def test_missing_ai_disclosure_rejected(self):
        d=copy.deepcopy(self.data);d["disclosures"]["ai_assistance"]=""
        self.assertTrue(errors(d))
    def test_markdown_regeneration_contract(self):
        self.assertEqual(self.markdown,render_markdown(self.data))
    def test_invalid_markdown_rejected(self):
        self.assertTrue(errors(self.data,self.markdown+"\nstale"))
if __name__=="__main__":unittest.main()
