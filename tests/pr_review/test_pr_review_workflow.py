import json
import os
import pathlib
import subprocess

import pytest
import yaml

WORKFLOW = pathlib.Path(".github/workflows/pr-review.yml")
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


def steps(job):
    return yaml.safe_load(WORKFLOW.read_text())["jobs"][job]["steps"]


def review_output(findings, summary="Adds contact export."):
    return json.dumps({"summary": summary, "findings": findings})


@pytest.fixture(scope="module")
def post_script(tmp_path_factory):
    path = tmp_path_factory.mktemp("pr_review") / "post.js"
    path.write_text(steps("post")[0]["with"]["script"])
    return path


def run_post(post_script, result, scope="full", failures=()):
    scenario = {
        "env": {"RESULT": result, "BASE_SHA": BASE, "SCOPE": scope, "HEAD_SHA": HEAD},
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
    script = next(s for s in steps("review") if s.get("id") == "range")["run"]
    output = cwd / "github_output"
    output.write_text("")
    env = {
        **os.environ,
        "GITHUB_OUTPUT": str(output),
        "EVENT_ACTION": action,
        "BEFORE_SHA": before,
        "PR_BASE_SHA": base,
    }
    subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        cwd=cwd, env=env, check=True,
    )
    return dict(line.split("=", 1) for line in output.read_text().splitlines())


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
