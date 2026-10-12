import json
import os
import pathlib
import subprocess

import pytest
import yaml

PR_WORKFLOW = pathlib.Path(".github/workflows/pr-review.yml")
DOC_WORKFLOW = pathlib.Path(".github/workflows/doc-review.yml")
HARNESS = pathlib.Path(__file__).with_name("run_post_script.mjs")
BASE = "a" * 40
HEAD = "b" * 40
FINDING = {
    "path": "src/services.py",
    "line": 31,
    "severity": "high",
    "title": "Email check is inverted",
    "body": "Valid emails are rejected.",
}


def load(workflow):
    return yaml.safe_load(workflow.read_text())


def steps(job, workflow=PR_WORKFLOW):
    return load(workflow)["jobs"][job]["steps"]


def step(job, step_id, workflow=PR_WORKFLOW):
    return next(s for s in steps(job, workflow) if s.get("id") == step_id)


def without(mapping, *keys):
    return {k: v for k, v in mapping.items() if k not in keys}


def run_bash_step(script, cwd, env):
    output = cwd / "github_output"
    output.write_text("")
    subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        cwd=cwd, env={**os.environ, "GITHUB_OUTPUT": str(output), **env}, check=True,
    )
    return dict(line.split("=", 1) for line in output.read_text().splitlines())


def review_output(findings, summary="Adds contact export."):
    return json.dumps({"summary": summary, "findings": findings})


# --- Posting script (shared by both workflows) ---


@pytest.fixture(scope="module")
def post_script(tmp_path_factory):
    path = tmp_path_factory.mktemp("pr_review") / "post.js"
    path.write_text(steps("post")[0]["with"]["script"])
    return path


def run_post(post_script, result, scope="full", failures=(), title="AI review"):
    scenario = {
        "env": {"RESULT": result, "BASE_SHA": BASE, "SCOPE": scope, "HEAD_SHA": HEAD, "TITLE": title},
        "createReviewFailures": list(failures),
    }
    out = subprocess.run(
        ["node", str(HARNESS), str(post_script)],
        input=json.dumps(scenario),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def test_findings_are_posted_as_inline_review_comments(post_script):
    out = run_post(post_script, review_output([FINDING]))

    assert out["error"] is None
    [call] = out["calls"]
    assert call["method"] == "pulls.createReview"
    args = call["args"]
    assert args["event"] == "COMMENT"
    assert args["commit_id"] == HEAD
    assert args["pull_number"] == 7
    assert args["body"] == "### AI review — full PR\n\nAdds contact export."
    assert args["comments"] == [{
        "path": "src/services.py",
        "line": 31,
        "side": "RIGHT",
        "body": "**[high] Email check is inverted**\n\nValid emails are rejected.",
    }]


def test_delta_review_header_names_the_commit_range(post_script):
    out = run_post(post_script, review_output([FINDING]), scope="delta")

    assert out["calls"][0]["args"]["body"].startswith("### AI review — new commits aaaaaaa..bbbbbbb")


def test_header_uses_the_title_from_the_environment(post_script):
    full = run_post(post_script, review_output([FINDING]), title="Docs review")
    delta = run_post(post_script, review_output([FINDING]), scope="delta", title="Docs review")
    raw = run_post(post_script, "not json at all", title="Docs review")

    assert full["calls"][0]["args"]["body"].startswith("### Docs review — full PR")
    assert delta["calls"][0]["args"]["body"].startswith("### Docs review — new commits aaaaaaa..bbbbbbb")
    assert raw["calls"][0]["args"]["body"].startswith("### Docs review\n")


def test_line_outside_the_diff_falls_back_to_a_body_only_review(post_script):
    out = run_post(post_script, review_output([FINDING]), failures=[422])

    assert out["error"] is None
    first, second = out["calls"]
    assert "comments" in first["args"]
    assert "comments" not in second["args"]
    assert second["args"]["body"].endswith(
        "- `src/services.py:31` **[high] Email check is inverted** — Valid emails are rejected."
    )


def test_other_github_errors_fail_the_job(post_script):
    out = run_post(post_script, review_output([FINDING]), failures=[500])

    assert out["error"]["status"] == 500
    assert len(out["calls"]) == 1


def test_clean_full_review_says_no_issues(post_script):
    out = run_post(post_script, review_output([]))

    [call] = out["calls"]
    assert call["method"] == "pulls.createReview"
    assert call["args"]["body"].endswith("No issues found.")
    assert "comments" not in call["args"]


def test_clean_delta_review_posts_nothing(post_script):
    out = run_post(post_script, review_output([]), scope="delta")

    assert out == {"calls": [], "error": None}


@pytest.mark.parametrize("result", ["not json at all", '{"text": "valid JSON, wrong shape"}'])
def test_output_that_does_not_match_the_schema_is_posted_raw(post_script, result):
    out = run_post(post_script, result)

    [call] = out["calls"]
    assert call["method"] == "issues.createComment"
    assert call["args"]["issue_number"] == 7
    assert call["args"]["body"].endswith(result)


def test_model_text_is_posted_verbatim_never_evaluated(post_script):
    nasty = {**FINDING, "body": "Try `${process.exit(1)}` and ${{ secrets.X }}"}
    out = run_post(post_script, review_output([nasty]))

    assert out["error"] is None
    assert out["calls"][0]["args"]["comments"][0]["body"].endswith("Try `${process.exit(1)}` and ${{ secrets.X }}")
    assert "${{" not in post_script.read_text()


# --- Review range step (shared by both workflows) ---


@pytest.fixture
def git_repo(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(message):
        (tmp_path / "file.txt").write_text(message)
        git("add", "file.txt")
        git("commit", "-q", "-m", message)
        return git("rev-parse", "HEAD")

    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    return tmp_path, git, commit


def run_range(cwd, action, before, base):
    script = step("review", "range")["run"]
    return run_bash_step(script, cwd, {"EVENT_ACTION": action, "BEFORE_SHA": before, "PR_BASE_SHA": base})


def test_new_pr_reviews_the_full_pr(git_repo):
    cwd, _, commit = git_repo
    base = commit("base")
    commit("feature")

    assert run_range(cwd, "opened", "", base) == {"base": base, "scope": "full"}


def test_push_to_pr_reviews_only_the_new_commits(git_repo):
    cwd, _, commit = git_repo
    base = commit("base")
    before = commit("first push")
    commit("second push")

    assert run_range(cwd, "synchronize", before, base) == {"base": before, "scope": "delta"}


def test_force_push_with_rewritten_history_reviews_the_full_pr(git_repo):
    cwd, git, commit = git_repo
    base = commit("base")
    before = commit("first push")
    git("reset", "-q", "--hard", base)
    commit("rewritten push")

    assert run_range(cwd, "synchronize", before, base) == {"base": base, "scope": "full"}


def test_force_push_with_unknown_before_sha_reviews_the_full_pr(git_repo):
    cwd, _, commit = git_repo
    base = commit("base")
    commit("rewritten push")

    assert run_range(cwd, "synchronize", "c" * 40, base) == {"base": base, "scope": "full"}


# --- Docs review workflow ---


@pytest.mark.parametrize("workflow, title", [(PR_WORKFLOW, "AI review"), (DOC_WORKFLOW, "Docs review")])
def test_each_workflow_posts_under_its_own_title(workflow, title):
    assert steps("post", workflow)[0]["env"]["TITLE"] == title


def test_doc_review_shares_its_plumbing_with_pr_review():
    pr, doc = load(PR_WORKFLOW), load(DOC_WORKFLOW)
    pr_review, doc_review = pr["jobs"]["review"], doc["jobs"]["review"]
    pr_post, doc_post = pr["jobs"]["post"], doc["jobs"]["post"]

    assert doc[True] == pr[True]  # PyYAML reads the `on:` key as True
    assert "concurrency" not in doc
    for key in ("if", "runs-on", "timeout-minutes", "permissions", "outputs"):
        assert doc_review[key] == pr_review[key], key
    assert doc_review["steps"][0] == pr_review["steps"][0]  # checkout
    assert step("review", "range", DOC_WORKFLOW) == step("review", "range", PR_WORKFLOW)
    doc_codex = step("review", "codex", DOC_WORKFLOW)
    pr_codex = step("review", "codex", PR_WORKFLOW)
    assert doc_codex["uses"] == pr_codex["uses"]
    assert without(doc_codex["with"], "prompt") == without(pr_codex["with"], "prompt")
    for key in ("needs", "if", "runs-on", "permissions"):
        assert doc_post[key] == pr_post[key], key
    assert doc_post["steps"][0]["uses"] == pr_post["steps"][0]["uses"]
    assert doc_post["steps"][0]["with"]["script"] == pr_post["steps"][0]["with"]["script"]
    assert without(doc_post["steps"][0]["env"], "TITLE") == without(pr_post["steps"][0]["env"], "TITLE")


def run_find_docs(cwd, docs_path):
    return run_bash_step(step("review", "docs", DOC_WORKFLOW)["run"], cwd, {"DOCS_PATH": docs_path})


def test_docs_are_found_when_the_directory_exists(tmp_path):
    (tmp_path / "handbook").mkdir()

    assert run_find_docs(tmp_path, "handbook") == {"path": "handbook"}


def test_nothing_is_found_without_the_directory(tmp_path):
    assert run_find_docs(tmp_path, "documentation") == {}


def test_docs_path_defaults_to_documentation():
    assert step("review", "docs", DOC_WORKFLOW)["env"]["DOCS_PATH"] == "${{ vars.DOCS_PATH || 'documentation' }}"


def test_codex_runs_only_when_docs_were_found():
    review_steps = steps("review", DOC_WORKFLOW)
    ids = [s.get("id") for s in review_steps]

    assert ids.index("range") < ids.index("docs") < ids.index("codex")
    assert step("review", "codex", DOC_WORKFLOW)["if"] == "steps.docs.outputs.path != ''"
