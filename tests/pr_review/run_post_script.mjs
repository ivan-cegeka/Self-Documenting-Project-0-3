// Runs the github-script body from pr-review.yml against a mocked GitHub client.
// Usage: node run_post_script.mjs <script-file>   (scenario JSON on stdin)
// Prints {"calls": [...], "error": null | {"message", "status"}} as JSON.
import { readFileSync } from "fs";

const script = readFileSync(process.argv[2], "utf8");
const scenario = JSON.parse(readFileSync(0, "utf8"));
const createReviewFailures = [...(scenario.createReviewFailures || [])];
const calls = [];

const github = {
  rest: {
    pulls: {
      createReview: async (args) => {
        calls.push({ method: "pulls.createReview", args });
        const status = createReviewFailures.shift();
        if (status) {
          const error = new Error(`HTTP ${status}`);
          error.status = status;
          throw error;
        }
        return { data: {} };
      },
    },
    issues: {
      createComment: async (args) => {
        calls.push({ method: "issues.createComment", args });
        return { data: {} };
      },
    },
  },
};
const context = {
  repo: { owner: "acme", repo: "crm" },
  payload: { pull_request: { number: 7 } },
};
Object.assign(process.env, scenario.env);

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
let error = null;
try {
  await new AsyncFunction("github", "context", script)(github, context);
} catch (e) {
  error = { message: e.message, status: e.status ?? null };
}
process.stdout.write(JSON.stringify({ calls, error }));