# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState
from botbuilder.schema import ChannelAccount, ConversationReference, Activity

from user_profile import UserProfile
from conversation_data import ConversationData

from srefunctions import SreFunctions

from openai import AzureOpenAI
import os
from typing import Dict 
import json

systemMessage = "Você é um bot que lida com questões relacionadas a SRE. Responda às perguntas do usuário sobre SRE e, se necessário, peça mais informações para fornecer uma resposta mais precisa."


client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_VERSION",""),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE","").strip(),
    api_key = os.getenv("AZURE_OPENAI_API_KEY","").strip(),
)

class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    def __init__(self, conversation_state: ConversationState, user_state: UserState, conversation_references: Dict[str, ConversationReference]):
        if conversation_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.conversation_data_accessor = self.conversation_state.create_property(
            "ConversationData"
        )
        self.user_profile_accessor = self.user_state.create_property("UserProfile")
        self.conversation_references = conversation_references

    async def on_message_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )
        if (turn_context.activity.text == "/clear"):
            conversation_data.messages = []
            await turn_context.send_activity("Conversa apagada")
            return
        
        if (len(conversation_data.messages) == 0):
            conversation_data.messages.append({ "role": "system", "content" : systemMessage })
        conversation_data.messages.append({ "role": "user", "content" : turn_context.activity.text })
        await self.function_call(conversation_data, turn_context)

    async def proactiveMessage(self, turn_context: TurnContext, body):
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )
        #print (conversation_data.messages)
        bodyText = json.dumps(body)
        if (len(conversation_data.messages) == 0):
            conversation_data.messages.append({ "role": "system", "content" : systemMessage })
        conversation_data.messages.append({ "role": "user", "content" : "Evento externo recebido: \n```json\n" + bodyText  + "\n```" })
        await self.conversation_state.save_changes(turn_context)
        return await turn_context.send_activity("Evento externo recebido. O que deseja saber sobre ele?")

    async def on_turn(self, turn_context: TurnContext):
        #print("on_turn")
        await super().on_turn(turn_context)
        #print("on_turn2")

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    def _add_conversation_reference(self, activity: Activity):
        """
        This populates the shared Dictionary that holds conversation references. In this sample,
        this dictionary is used to send a message to members when /api/notify is hit.
        :param activity:
        :return:
        """
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[
            conversation_reference.user.id
        ] = conversation_reference

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        #print('on_conversation_update_activity')
        self._add_conversation_reference(turn_context.activity)
        return await super().on_conversation_update_activity(turn_context)
    
    async def function_call(self, conversation_data, turn_context):
        try:
            functionsObject = SreFunctions(turn_context)
            functions = functionsObject.get_openai_functions()
            tools = None
            #check if the first position of function has an attribute named "type"
            if hasattr(functions[0], "type"):
                tools = functions
            else :
                tools = []
                for function in functions:
                    tools.append({"type": "function", "function": function})


            #print('calling 1')
            #for message in chat_context["conversation"]:
            #    print(message["role"])
            #    print(message["content"])
            
            response_message = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_data.messages,
                tools=tools,
                tool_choice="auto", 
            ).choices[0].message
            #print(response_message)
            if response_message.tool_calls is not None:
                conversation_data.messages.append( # adding assistant response to messages
                    todict(response_message)
                )
                #sending assistant response to user if present
                if (response_message.content is not None):
                    await turn_context.send_activity(response_message.content)

                for tool_call in response_message.tool_calls:
                        # Call the function. The JSON response may not always be valid so make sure to handle errors
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    realFunction = getattr(functionsObject, function_name)
                    function_response = await realFunction(**function_args)
                    conversation_data.messages.append( # adding function response to messages
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    ) 
                return await self.function_call(conversation_data, turn_context)
            else:
                #print("not function")
                conversation_data.messages.append( # adding assistant response to messages
                    {
                        "role": response_message.role,
                        "content": response_message.content,
                    }
                )
                await turn_context.send_activity(response_message.content)
                return 
        except Exception as e:
            print(e)
            await turn_context.send_activity("Ocorreu um erro: " + str(e))
            return


def todict(obj):
    tool_calls = None
    if (obj.tool_calls is not None):
        tool_calls = []
        for tool_call in obj.tool_calls:
            tool_calls.append({"id": tool_call.id, "function": {"name": tool_call.function.name, "arguments": tool_call.function.arguments}, "type": tool_call.type})
    return {"content": obj.content, "role": obj.role, "tool_calls": tool_calls}