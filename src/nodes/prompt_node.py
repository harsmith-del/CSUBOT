from typing import Dict, List, Optional, Tuple, Union, Any

from haystack.nodes import PromptNode
from haystack.schema import Document, MultiLabel
from haystack.nodes.prompt import PromptTemplate

class PromptNodeWrapped(PromptNode):
    """wraps haystack prompt node to provide consitent output with 
    transformer summarization node"""
    def run(
        self,
        query: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        labels: Optional[MultiLabel] = None,
        documents: Optional[List[Document]] = None,
        meta: Optional[dict] = None,
        invocation_context: Optional[Dict[str, Any]] = None,
        prompt_template: Optional[Union[str, PromptTemplate]] = None,
    ) -> Tuple[Dict, str]:
        result = super().run(
            query,
            file_paths,
            labels,
            documents,
            meta,
            invocation_context,
            prompt_template,
        )
        #copy generated summary to document for consistency with transformer_summarization node 
        result[0]['invocation_context']['documents'][0].meta['summary'] = result[0]['answers'][0].answer
        return result