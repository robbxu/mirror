import pandas as pd
from math import floor
import json
import phoenix as px
from phoenix.trace import SpanEvaluations
from phoenix.evals import HallucinationEvaluator, OpenAIModel, QAEvaluator, run_evals

eval_model = OpenAIModel(model="gpt-4o", timeout=600)

# Define your evaluators
hallucination_evaluator = HallucinationEvaluator(eval_model)
# qa_evaluator = QAEvaluator(eval_model)

client = px.Client()
# Load all spans into a dataframe

def process_input(row):
    messages = row["attributes.llm.input_messages"]
    if messages is None:
        return ""

    message_texts = [item["message.content"] for item in messages]
    result = message_texts[-1]
    if '\"writing_samples\":' in result:
        result = result.split(',\"writing_samples\":')[0]
        result = result.split('{\"message\":')[1]
    return result

def process_reference(row):
    messages = row["attributes.llm.input_messages"]

    if messages is None:
        return ""

    message_texts = [item["message.content"] for item in messages]
    for message in message_texts:
        if '\nSchema:\n{\"topics\":' in message:
            return message.split('\nSchema:\n{\"topics\":')[1]
        elif '\"writing_samples\":' in message:
            return message.split('\"writing_samples\":')[1]
    return "No reference found."

def process_output(row):
    obj = json.loads(row["attributes.output.value"])
    text = obj["generations"][0][0]["text"]
    return text


def main():
    spans_df = client.get_spans_dataframe("parent_id is not None")
    spans_df["message"] = spans_df["attributes.llm.input_messages"]
    spans_df['span_id'] = spans_df["context.span_id"]

    spans_df["reference"] = spans_df.apply(process_reference, axis=1)
    spans_df["output"] = spans_df.apply(process_output, axis=1)
    spans_df["input"] = spans_df.apply(process_input, axis=1)

    df = spans_df[["span_id", "reference", "input", "output"]].copy()
    # print(df)
    df = df.head(14)
    hallucination_eval_df_list = run_evals(
        dataframe=df, evaluators=[hallucination_evaluator], provide_explanation=True
    )
    hallucination_eval_df = hallucination_eval_df_list[0]
    
    results_df = df.copy()
    results_df["label"] = hallucination_eval_df["label"]
    results_df["explanation"] = hallucination_eval_df["explanation"]
    # results_df["qa_eval"] = qa_eval_df["label"]
    # results_df["qa_explanation"] = qa_eval_df["explanation"]
    print(results_df)

    client.log_evaluations(
        SpanEvaluations(
            dataframe=results_df,
            eval_name="Hallucination Evaluation",
        ),
    )

if __name__ == "__main__":
    main()
