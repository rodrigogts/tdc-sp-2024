from datetime import date;

fakeLogs = """
Exception Ocurred: Database connection error: Connection timed out. URL: myazuredb.database.windows.net
Exception Ocurred: Database connection error: Connection timed out. URL: myazuredb.database.windows.net
Exception Ocurred: Database connection error: Connection timed out. URL: myazuredb.database.windows.net
Exception Ocurred: Database connection error: Connection timed out. URL: myazuredb.database.windows.net
"""

databaseStatus = "stopped"


class SreFunctions:
    def __init__(self, turn_context):
        self.turn_context = turn_context

    async def restart_application(self, resource_group_name, webapp_name):
        await self.turn_context.send_activity("Restarting application: " + resource_group_name +"/" +  webapp_name)
        return "Application restarted successfully"
    
    async def start_application(self, resource_group_name, webapp_name):
        await self.turn_context.send_activity("Starting application: " + resource_group_name +"/" +  webapp_name)
        return "Application started successfully"
    
    async def stop_application(self, resource_group_name, webapp_name):
        await self.turn_context.send_activity("Stopping application: " + resource_group_name +"/" +  webapp_name)
        return "Application stopped successfully"
    
    async def get_application_status(self, resource_group_name, webapp_name):
        await self.turn_context.send_activity("Getting application status: " + resource_group_name +"/" +  webapp_name)
        return "Application is running"
    
    async def get_application_logs(self, resource_group_name, webapp_name, from_time = None, to_time = None):
        await self.turn_context.send_activity("Getting application logs: " + resource_group_name +"/" +  webapp_name)
        return fakeLogs
    
    async def get_database_status(self, database_url):
        await self.turn_context.send_activity("Getting database status: " + database_url)
        return "Database is " + databaseStatus
    
    async def start_database(self, database_url):
        await self.turn_context.send_activity("Starting database: " + database_url)
        databaseStatus = "running"
        return "Database started successfully"

    async def stop_database(self, database_url):
        await self.turn_context.send_activity("Stopping database: " + database_url)
        databaseStatus = "stopped"
        return "Database stopped successfully"

    
    @staticmethod
    def get_openai_functions():
        return [  
            {
                "name": "restart_application",
                "description": "Restart and Web Application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group_name": {
                            "type": "string",
                            "description": "Resource Group Name"
                        },
                        "webapp_name": {
                            "type": "string",
                            "description": "Web Application Name"
                        }
                    },
                    "required": ["resource_group_name", "webapp_name"],
                }
            },
            {
                "name": "start_application",
                "description": "Start a Web Application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group_name": {
                            "type": "string",
                            "description": "Resource Group Name"
                        },
                        "webapp_name": {
                            "type": "string",
                            "description": "Web Application Name"
                        }
                    },
                    "required": ["resource_group_name", "webapp_name"],
                }
            },
            {
                "name": "stop_application",
                "description": "Stop a Web Application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group_name": {
                            "type": "string",
                            "description": "Resource Group Name"
                        },
                        "webapp_name": {
                            "type": "string",
                            "description": "Web Application Name"
                        }
                    },
                    "required": ["resource_group_name", "webapp_name"],
                }
            },
            {
                "name": "get_application_status",
                "description": "Get the status of a Web Application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group_name": {
                            "type": "string",
                            "description": "Resource Group Name"
                        },
                        "webapp_name": {
                            "type": "string",
                            "description": "Web Application Name"
                        }
                    },
                    "required": ["resource_group_name", "webapp_name"],
                }
            },
            {
                "name": "get_application_logs",
                "description": "Get the logs of a Web Application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group_name": {
                            "type": "string",
                            "description": "Resource Group Name"
                        },
                        "webapp_name": {
                            "type": "string",
                            "description": "Web Application Name"
                        },
                        "from_time": {
                            "type": "string",
                            "description": "From Time"
                        },
                        "to_time": {
                            "type": "string",
                            "description": "To Time"
                        }
                    },
                    "required": ["resource_group_name", "webapp_name"],
                }
            },
            {
                "name": "get_database_status",
                "description": "Get the status of a Database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database_url": {
                            "type": "string",
                            "description": "Database URL"
                        }
                    },
                    "required": ["database_url"],
                }
            },
            {
                "name": "start_database",
                "description": "Start a Database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database_url": {
                            "type": "string",
                            "description": "Database URL"
                        }
                    },
                    "required": ["database_url"],
                }
            },
            {
                "name": "stop_database",
                "description": "Stop a Database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database_url": {
                            "type": "string",
                            "description": "Database URL"
                        }
                    },
                    "required": ["database_url"],
                }
            }
            
        ]  


