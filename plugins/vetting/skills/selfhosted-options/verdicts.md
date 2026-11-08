# Evaluation verdicts — self-hosted tools

Completed `selfhosted-options` runs. **Start from these rather than re-running the sweep** — re-check only what has aged. Verdicts depend on what was already deployed at the time, so re-read the reasoning before reusing a call.

_(Empty — this instance has not run a sweep yet.)_


## Lessons that held across evaluations

- **A "dead project" can be an infrastructure fault.** A tool whose scheduled jobs all showed "Failed" for a
  month looked abandoned; the real cause was the backing store crashing under its job queue. Rule out your own
  deployment before judging the project.
- **Check the code, not the reputation, and not the landscape sweep.** A tool sold as a "simple counter" had
  funnels, retention and session replay in its source, ungated when self-hosted.
- **Sentiment and code can disagree, and the code wins.** Heavy-user abandonment stories did not generalise when
  the one documented migration target was architecturally worse at that scale.
- **A slop accusation is a hypothesis to test**: commit-author trailers, test files, distinct issue authors, and
  whether the accuser had any evidence.
- **Auth that is opt-in is no auth on a fresh install**, and "no authentication by design" means it must sit
  behind your own gateway.
- **Static review proves little about scale.** Say "nothing was stood up and run" when that is true.
- **Popularity and quality rankings can be close to unrelated** in a young field; most candidates cannot run
  unattended, which is the thing none of them advertise clearly.
