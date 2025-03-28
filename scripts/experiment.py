import os
import pandas as pd
from dotenv import load_dotenv
import phoenix as px
from phoenix.evals import OpenAIModel, llm_classify
from phoenix.experiments import run_experiment
from phoenix.experiments.types import Example


# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server', 'backend', 'env', '.env.dev')
load_dotenv(env_path)

experiment_model = OpenAIModel(model="gpt-4o", timeout=600)

# Initialize a phoenix client
client = px.Client()
# Get the current dataset version. You can omit the version for the latest.
dataset = client.get_dataset(name="Styles Eval")

CATEGORICAL_TEMPLATE = ''' You are comparing a sample text to an output text created by an LLM. You are trying to determine
whether the output text matches the writing style of the sample text. Here is the data:
    [BEGIN DATA]
    ************
    [Sample text]: {sample}
    ************
    [Output text]: {output}
    [END DATA]

Compare the Sample text above to the Output text. You must determine whether the Output text
matches the writing style of the Sample text. Please focus on factors like writing style, sentence complexity, tone, 
and other writing characteristics. Be flexible in your evaluation to account for different slight variation depending on subject matter.
Your response must be single word, either "match" or "mismatch",
and should not contain any text or characters aside from that word.
"mismatch" means that the output text does not match the writing style of the sample text.
"match" means the output text matches the writing style of the sample text. 

Here is an example of a match:
Sample: 'They gradually realize they actually do have feelings for each other. It was heartwarming and definitely one of the best dramas I’ve seen. The emotions on display and how human the characters felt was top notch. Definitely one to recommend.'
Output: 'I strive to be similar on the mats. When you watch a tiger hunt, you're seeing death in motion. They're powerful, but also calculating. It's like watching a high-level grappling match play out in nature. It's similar to why I like BJJ. Tigers embody that authentic, primal power that you can't help but respect.'

Here is an example of a mismatch:
Sample: 'On the Dovish front, we’ve decided to start developing the front-end ourselves instead of sitting around waiting for VC money to fall from the sky. That’s a direction I’m much more comfortable with, and it’s definitely giving us more agency over our fate. I’m looking forward to getting this done, especially since I have a feeling that in the process it will help us solidify what the product should even look like.'
Output: 'Each challenge we face is an opportunity to forge ourselves into something greater while maintaining our compassion and heart. The meaning isn't in some grand cosmic plan - it's in showing up every day, supporting the people we care about, and facing our fears head-on with everything we've got. This life might be temporary, might be just a dream, but the growth we achieve and the bonds we build feel real and significant.'
'''

# Define your task
# Typically should be an LLM call or a call to your application
def task(example: Example) -> str:
    data = {"sample": [example.input['sample']], "output": [example.input['output']]}
    dataframe = pd.DataFrame.from_dict(data)
    rails = ["match", "mismatch"]
    result = llm_classify(
        dataframe=dataframe,
        model=experiment_model,
        template=CATEGORICAL_TEMPLATE, 
        rails=rails
    )
    return result["label"].iloc[0]


# Define an evaluator. This just an example.
def match(output, expected) -> float:
    return expected["label"] == output

# Store the evaluators for later use
evaluators = [match]

# Run an experiment
experiment = run_experiment(dataset, task, evaluators=evaluators)

# Print the experiment results
print(experiment)
