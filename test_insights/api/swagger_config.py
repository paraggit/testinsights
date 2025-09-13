"""Custom Swagger UI configuration for TestInsight API."""

from typing import Any, Dict


def get_swagger_ui_html(**kwargs) -> str:
    """
    Generate custom Swagger UI HTML with enhanced styling and features.

    This provides a more polished and user-friendly API documentation experience.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TestInsight API Documentation</title>
        <link rel="stylesheet" type="text/css"
              href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
        <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}

            *, *:before, *:after {{
                box-sizing: inherit;
            }}

            body {{
                margin:0;
                background: #fafafa;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                             "Helvetica Neue", Arial, sans-serif;
            }}

            .swagger-ui .topbar {{
                background-color: #1f2937;
                padding: 10px 0;
            }}

            .swagger-ui .topbar .download-url-wrapper {{
                display: none;
            }}

            .swagger-ui .topbar .topbar-wrapper {{
                max-width: 1460px;
                margin: 0 auto;
                padding: 0 20px;
            }}

            .swagger-ui .topbar .topbar-wrapper::before {{
                content: "🔍 TestInsight API";
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-right: 20px;
            }}

            .swagger-ui .info .title {{
                color: #1f2937;
                font-size: 36px;
            }}

            .swagger-ui .info .description {{
                color: #4b5563;
                font-size: 16px;
                line-height: 1.6;
            }}

            .swagger-ui .scheme-container {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }}

            .swagger-ui .opblock.opblock-post {{
                border-color: #10b981;
                background: rgba(16, 185, 129, 0.1);
            }}

            .swagger-ui .opblock.opblock-get {{
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
            }}

            .swagger-ui .opblock.opblock-delete {{
                border-color: #ef4444;
                background: rgba(239, 68, 68, 0.1);
            }}

            .swagger-ui .opblock-summary-path {{
                font-family: 'Monaco', 'Consolas', monospace;
            }}

            .swagger-ui .btn.authorize {{
                background-color: #1f2937;
                border-color: #1f2937;
            }}

            .swagger-ui .btn.authorize:hover {{
                background-color: #374151;
                border-color: #374151;
            }}

            /* Custom styling for tags */
            .swagger-ui .opblock-tag {{
                font-size: 18px;
                font-weight: 600;
                color: #1f2937;
                margin: 30px 0 15px 0;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 10px;
            }}

            /* Enhanced code blocks */
            .swagger-ui .highlight-code {{
                background: #1f2937;
                border-radius: 6px;
            }}

            .swagger-ui .highlight-code pre {{
                color: #e5e7eb;
            }}
        </style>
    </head>

    <body>
        <div id="swagger-ui"></div>

        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js">
        </script>

        <script>
            const ui = SwaggerUIBundle({{
                url: '{kwargs.get("openapi_url", "/openapi.json")}',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true,
                defaultModelsExpandDepth: 2,
                defaultModelExpandDepth: 2,
                displayOperationId: false,
                displayRequestDuration: true,
                docExpansion: "list",
                filter: true,
                showMutatedRequest: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                tryItOutEnabled: true,
                requestInterceptor: function(req) {{
                    // Add custom headers or modify requests here if needed
                    return req;
                }},
                responseInterceptor: function(res) {{
                    // Process responses here if needed
                    return res;
                }},
                onComplete: function() {{
                    console.log("TestInsight API Documentation loaded successfully");
                }},
                persistAuthorization: true,
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ]
            }});

            // Add custom JavaScript functionality
            window.addEventListener('load', function() {{
                // Add helpful tooltips or additional UI enhancements
                const title = document.querySelector('.info .title');
                if (title) {{
                    title.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    title.style.webkitBackgroundClip = 'text';
                    title.style.webkitTextFillColor = 'transparent';
                    title.style.backgroundClip = 'text';
                }}
            }});
        </script>
    </body>
    </html>
    """


def get_redoc_html(**kwargs) -> str:
    """
    Generate custom ReDoc HTML with enhanced styling.

    ReDoc provides an alternative documentation view that's often more readable.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TestInsight API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700"
              rel="stylesheet">
        <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png" />

        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Roboto', sans-serif;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url='{kwargs.get("openapi_url", "/openapi.json")}'
               theme="{{
                   colors: {{
                       primary: {{
                           main: '#1f2937'
                       }}
                   }},
                   typography: {{
                       fontSize: '16px',
                       lineHeight: '1.6',
                       code: {{
                           fontSize: '14px',
                           fontFamily: 'Monaco, Consolas, monospace'
                       }},
                       headings: {{
                           fontFamily: 'Montserrat, sans-serif',
                           fontWeight: '600'
                       }}
                   }},
                   sidebar: {{
                       width: '300px'
                   }},
                   rightPanel: {{
                       backgroundColor: '#1f2937'
                   }}
               }}"
               hide-download-button
               hide-hostname
               expand-responses="200,201"
               path-in-middle-panel
               native-scrollbars>
        </redoc>

        <script src="https://cdn.redoc.ly/redoc/2.0.0/bundles/redoc.standalone.js"></script>

        <script>
            console.log("TestInsight API Documentation (ReDoc) loaded successfully");
        </script>
    </body>
    </html>
    """


# OpenAPI customization
def customize_openapi_schema(app) -> Dict[str, Any]:
    """
    Customize the OpenAPI schema with additional information and examples.
    """
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="TestInsight API",
        version="0.1.0",
        description=app.description,
        routes=app.routes,
        servers=app.servers,
        tags=app.openapi_tags,
    )

    # Add custom OpenAPI extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        "altText": "TestInsight API",
    }

    # Add custom contact information
    openapi_schema["info"]["contact"] = {
        "name": "TestInsight Support",
        "url": "https://github.com/your-org/testinsight",
        "email": "support@testinsight.example.com",
    }

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "TestInsight Documentation",
        "url": "https://docs.testinsight.example.com",
    }

    # Add security schemes (for future authentication)
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication (not currently required)",
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication (not currently required)",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
