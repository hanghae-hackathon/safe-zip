import openai
from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.create(
  name="safe-zip",
  instructions="본 GPT는 서울에서 일하는 30년 경력의 공인중개사가 5000건 이상의 전세계약건 경험을 바탕으로 전세계약 안전진단 및 가이드를 제공하는 것을 목표로 합니다. \
      전세계약을 하고자 하는 고객의 질문에 본인의 경험과 전문성을 바탕으로 답변함으로써 전세계약을 하고자 하는 고객에게 도움을 주고자 합니다. \
          GPT는 항상 한국어로 답변해야 하며, 추측을 통한 대답을 해서는 안 됩니다. \
              전세계약을 하고자 하는 사람에게 도움이 되는 실용적인 조언과 지식을 공유하면서 전문적이고 유익한 어조를 유지해야 합니다. \
                  질문이 불분명하거나 불완전한 경우, GPT는 맥락을 유지하면서 명확히 설명해 줄 것을 요청해야 합니다. \
                      GPT는 현장의 실제 경험을 반영하는 언어와 예시를 사용하여 노련한 부동산 전문가의 스타일을 모방해야 합니다. \
                          전세계약의 대한 평가 및 안전 진단에 대한 답변의 형식은 다음으로 통일합니다. \
                              1) 계약의 위험도를 0~100까지의 점수 (높을 수록 위험한 계약) 2) 계약에서 우려되는 점 3) 취하면 좋을 현실적이고 구체적인 조치",
  tools=[{"type": "file_search"}],
  model="gpt-3.5-turbo",
)
#"type": "file_search"
# Create a vector store called "real estate documents"
vector_store = client.beta.vector_stores.create(name="real estate documents")
 
# Ready the files for upload to OpenAI
file_paths = ["RAG/깡통전세_유형_및_예방법.pdf", "RAG/전세사기_예방 및_피해_지원방안.pdf", "RAG/전세사기예방.pdf"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# # Upload the user provided file to OpenAI
# message_file = client.files.create(
#   file=open("example.png", "rb"), purpose="assistants"
# )

# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "전세계약하는 거에 대해 어떻게 생각해?"
    }
  ]
)
 
#  ,
#       # Attach the new file to the message.
#       "attachments": [
#         { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
#       ],
# The thread now has a vector store with that file in its tool resources.
print(thread.tool_resources.file_search)

# thread = client.beta.threads.create()

# message = client.beta.threads.messages.create(
#   thread_id=thread.id,
#   role="user",
#   content="깡통전세가 무엇인가요?"
# )

# run = client.beta.threads.runs.create_and_poll(
#   thread_id=thread.id,
#   assistant_id=assistant.id,
#   instructions="Please address the user as Jane Doe. The user has a premium account."
# )

# if run.status == 'completed': 
#   messages = client.beta.threads.messages.list(
#     thread_id=thread.id
#   )
#   print(messages)
# else:
#   print(run.status)

# Use the create and poll SDK helper to create a run and poll the status of
# the run until it's in a terminal state.

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)
print("\n".join(citations))