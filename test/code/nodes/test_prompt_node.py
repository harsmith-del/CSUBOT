import sys

import pytest
from haystack import Pipeline
from haystack.schema import Document
from haystack.nodes import PromptModel

main_repo_path = '/usr/src/app'
if main_repo_path not in sys.path:
    sys.path.append(main_repo_path)

from nodes import PromptNodeWrapped


def test_run():    
    prompt_model = PromptModel()
    new_prompt_node = PromptNodeWrapped(prompt_model, default_prompt_template="question-answering-per-document")
    pipe = Pipeline()
    pipe.add_node(component=new_prompt_node, name="prompt_node", inputs=["Query"])

    doc_1 = "Contrails are a manmade type of cirrus cloud formed when water vapor from the exhaust of a jet engine condenses on particles, which come from either the surrounding air or the exhaust itself, and freezes, leaving behind a visible trail. The exhaust can also trigger the formation of cirrus by providing ice nuclei when there is an insufficient naturally-occurring supply in the atmosphere. One of the environmental impacts of aviation is that persistent contrails can form into large mats of cirrus, and increased air traffic has been implicated as one possible cause of the increasing frequency and amount of cirrus in Earth's atmosphere."
    doc_2 = "Because the aviation industry is especially sensitive to the weather, accurate weather forecasting is essential. Fog or exceptionally low ceilings can prevent many aircraft from landing and taking off. Turbulence and icing are also significant in-flight hazards. Thunderstorms are a problem for all aircraft because of severe turbulence due to their updrafts and outflow boundaries, icing due to the heavy precipitation, as well as large hail, strong winds, and lightning, all of which can cause severe damage to an aircraft in flight. Volcanic ash is also a significant problem for aviation, as aircraft can lose engine power within ash clouds. On a day-to-day basis airliners are routed to take advantage of the jet stream tailwind to improve fuel efficiency. Aircrews are briefed prior to takeoff on the conditions to expect en route and at their destination. Additionally, airports often change which runway is being used to take advantage of a headwind. This reduces the distance required for takeoff, and eliminates potential crosswinds."
    query = 'Why do airplanes leave contrails in the sky?'
    output = pipe.run(query=query, documents=[Document(doc_1), Document(doc_2)])
    assert output['invocation_context']['documents'][0].meta['summary'] == output['answers'][0].answer