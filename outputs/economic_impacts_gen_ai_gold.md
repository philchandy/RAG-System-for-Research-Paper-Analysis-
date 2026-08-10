# Generative AI at Work

## problem
- New generative AI tools have the potential to change how workers perform and learn, but little is known about their real-world impacts on the job, since prior evidence largely comes from lab-like settings rather than large-scale workplace deployment.
- The paper studies whether access to a generative AI conversational assistant changes worker productivity, and specifically whether it affects less-skilled/less-experienced workers differently than highly skilled, experienced workers — in contrast with earlier waves of computerization, which tended to favor higher-skill workers.

## method
- The authors study the staggered, agent-level rollout of a generative AI-based conversational assistant (built on a version of OpenAI's GPT models, further fine-tuned on customer-agent conversations) at a Fortune 500 enterprise software company's customer support operation.
- The tool monitors live customer chats and gives agents real-time suggested responses and links to internal documentation; agents retain full discretion to use, ignore, or edit the suggestions.
- The main causal estimates use a difference-in-differences regression with year-month and agent fixed effects, comparing agent productivity before and after AI access; standard errors are clustered at the agent level.
- To address concerns about heterogeneous/staggered treatment-effect bias in two-way fixed effects models, they also estimate dynamic treatment effects using the interaction-weighted (IW) estimator of Sun and Abraham (2021), and check robustness against other modern difference-in-differences estimators.

## dataset
- Data from 5,179 customer support agents and about 3 million chats at the data firm, with 1.2 million chats from 1,636 agents observed in the post-AI period; about 89% of agents are located outside the United States, mainly in the Philippines.
- Productivity outcomes measured per agent-month: resolutions per hour (RPH, the primary measure), average handle time (AHT), chats per hour (CPH), resolution rate (RR), and customer satisfaction via net promoter score (NPS).
- Customer and agent conversation sentiment is measured using SiEBERT, an LLM fine-tuned for sentiment analysis, scored on a scale from -1 to 1.

## results
- Access to the AI assistant increases average worker productivity (resolutions per hour) by about 14% overall; in the baseline two-way fixed effects model this is a 22.2% (0.47 chat) increase, falling to 13.8% (0.30 chat) once agent and tenure fixed effects are added.
- The productivity gains are highly uneven: less-skilled and less-experienced agents improve substantially, including a 34% increase in issues resolved per hour, with treated agents at two months of tenure performing as well as untreated agents with six-plus months of tenure; highly skilled and experienced agents see minimal productivity gains.
- Access to AI assistance improves customer sentiment (customer sentiment scores rise by about 0.18 points, roughly half a standard deviation) and reduces customer requests to escalate to a manager by about 25% relative to baseline.
- AI access is associated with roughly a 40% relative reduction in attrition among newer agents (under 6 months tenure) — about a 10 percentage point drop from a 25% baseline attrition rate — and workers retain some productivity gains even during AI system outages, suggesting durable learning.

## limitations
- The paper does not capture potential longer-term effects of generative AI on aggregate skill demand, job design, wages, or overall customer demand for the service. The data does not allow observing changes in wages, labor demand, or the skill composition of newly hired workers.
- The attrition results should be treated with more caution than the main productivity results, because agent fixed effects cannot be included (attrition can only occur once per worker), so the estimated attrition reduction may be overstated if AI access is preferentially given to agents the firm already expects to stay.
- The findings come from a single firm with a relatively stable product and customer service process, so the effects may not generalize to other firms, production processes, or types of generative AI deployment.
- The paper raises, but does not resolve, open questions about how top-performing workers should be compensated for the conversational data their work contributes to training the AI system.

## follow_up_questions

Answerable from the paper:
- Q: By how much did access to the AI assistant increase average worker productivity overall?
  A: About 14% (measured as resolutions per hour), or 13.8% in the model with agent and tenure fixed effects.
- Q: How much did productivity improve for novice/low-skilled workers specifically?
  A: A 34% increase in issues resolved per hour.
- Q: How many customer support agents and chats are in the study's dataset?
  A: 5,179 agents and about 3 million chats, including 1.2 million chats from 1,636 agents in the post-AI period.
- Q: How much did customer requests to speak with a manager decline after AI assistance was introduced?
  A: About a 25% relative decline.
- Q: What tool is used to measure sentiment in customer and agent conversations?
  A: SiEBERT, an LLM fine-tuned for sentiment analysis, scoring text from -1 to 1.

Not answered in the paper:
- Q: What are the aggregate employment or wage effects of generative AI across the whole economy?
  A: Not addressed — the paper explicitly states it is not designed to shed light on aggregate employment or wage effects.
- Q: What was the exact commercial cost of licensing or deploying the AI tool?
  A: Not reported in the paper.
- Q: How do these productivity effects generalize to industries outside customer support?
  A: Not studied — the paper only examines one customer service setting at one firm.
