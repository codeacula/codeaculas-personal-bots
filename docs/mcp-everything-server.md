# MCP Everything Server

## Program.cs

```csharp
using EverythingServer;
using EverythingServer.Prompts;
using EverythingServer.Tools;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModelContextProtocol;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

var builder = Host.CreateApplicationBuilder(args);
builder.Logging.AddConsole(consoleLogOptions =>
{
    // Configure all logs to go to stderr
    consoleLogOptions.LogToStandardErrorThreshold = LogLevel.Trace;
});

HashSet<string> subscriptions = [];
var _minimumLoggingLevel = LoggingLevel.Debug;

builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithTools<AddTool>()
    .WithTools<AnnotatedMessageTool>()
    .WithTools<EchoTool>()
    .WithTools<LongRunningTool>()
    .WithTools<PrintEnvTool>()
    .WithTools<SampleLlmTool>()
    .WithTools<TinyImageTool>()
    .WithPrompts<ComplexPromptType>()
    .WithPrompts<SimplePromptType>()
    .WithListResourceTemplatesHandler((ctx, ct) =>
    {
        return Task.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates =
            [
                new ResourceTemplate { Name = "Static Resource", Description = "A static resource with a numeric ID", UriTemplate = "test://static/resource/{id}" }
            ]
        });
    })
    .WithReadResourceHandler((ctx, ct) =>
    {
        var uri = ctx.Params?.Uri;

        if (uri is null || !uri.StartsWith("test://static/resource/"))
        {
            throw new NotSupportedException($"Unknown resource: {uri}");
        }

        int index = int.Parse(uri["test://static/resource/".Length..]) - 1;

        if (index < 0 || index >= ResourceGenerator.Resources.Count)
        {
            throw new NotSupportedException($"Unknown resource: {uri}");
        }

        var resource = ResourceGenerator.Resources[index];

        if (resource.MimeType == "text/plain")
        {
            return Task.FromResult(new ReadResourceResult
            {
                Contents = [new TextResourceContents
                {
                    Text = resource.Description!,
                    MimeType = resource.MimeType,
                    Uri = resource.Uri,
                }]
            });
        }
        else
        {
            return Task.FromResult(new ReadResourceResult
            {
                Contents = [new BlobResourceContents
                {
                    Blob = resource.Description!,
                    MimeType = resource.MimeType,
                    Uri = resource.Uri,
                }]
            });
        }
    })
    .WithSubscribeToResourcesHandler(async (ctx, ct) =>
    {
        var uri = ctx.Params?.Uri;

        if (uri is not null)
        {
            subscriptions.Add(uri);

            await ctx.Server.RequestSamplingAsync([
                new ChatMessage(ChatRole.System, "You are a helpful test server"),
                new ChatMessage(ChatRole.User, $"Resource {uri}, context: A new subscription was started"),
            ],
            options: new ChatOptions
            {
                MaxOutputTokens = 100,
                Temperature = 0.7f,
            },
            cancellationToken: ct);
        }

        return new EmptyResult();
    })
    .WithUnsubscribeFromResourcesHandler((ctx, ct) =>
    {
        var uri = ctx.Params?.Uri;
        if (uri is not null)
        {
            subscriptions.Remove(uri);
        }
        return Task.FromResult(new EmptyResult());
    })
    .WithCompleteHandler((ctx, ct) =>
    {
        var exampleCompletions = new Dictionary<string, IEnumerable<string>>
        {
            { "style", ["casual", "formal", "technical", "friendly"] },
            { "temperature", ["0", "0.5", "0.7", "1.0"] },
            { "resourceId", ["1", "2", "3", "4", "5"] }
        };

        if (ctx.Params is not { } @params)
        {
            throw new NotSupportedException($"Params are required.");
        }
        
        var @ref = @params.Ref;
        var argument = @params.Argument;

        if (@ref.Type == "ref/resource")
        {
            var resourceId = @ref.Uri?.Split("/").Last();

            if (resourceId is null)
            {
                return Task.FromResult(new CompleteResult());
            }

            var values = exampleCompletions["resourceId"].Where(id => id.StartsWith(argument.Value));

            return Task.FromResult(new CompleteResult
            {
                Completion = new Completion { Values = [..values], HasMore = false, Total = values.Count() }
            });
        }

        if (@ref.Type == "ref/prompt")
        {
            if (!exampleCompletions.TryGetValue(argument.Name, out IEnumerable<string>? value))
            {
                throw new NotSupportedException($"Unknown argument name: {argument.Name}");
            }

            var values = value.Where(value => value.StartsWith(argument.Value));
            return Task.FromResult(new CompleteResult
            {
                Completion = new Completion { Values = [..values], HasMore = false, Total = values.Count() }
            });
        }

        throw new NotSupportedException($"Unknown reference type: {@ref.Type}");
    })
    .WithSetLoggingLevelHandler(async (ctx, ct) =>
    {
        if (ctx.Params?.Level is null)
        {
            throw new McpException("Missing required argument 'level'");
        }

        _minimumLoggingLevel = ctx.Params.Level;

        await ctx.Server.SendNotificationAsync("notifications/message", new
            {
                Level = "debug",
                Logger = "test-server",
                Data = $"Logging level set to {_minimumLoggingLevel}",
            }, cancellationToken: ct);

        return new EmptyResult();
    })
    ;

builder.Services.AddSingleton(subscriptions);
builder.Services.AddHostedService<SubscriptionMessageSender>();
builder.Services.AddHostedService<LoggingUpdateMessageSender>();

builder.Services.AddSingleton<Func<LoggingLevel>>(_ => () => _minimumLoggingLevel);

await builder.Build().RunAsync();
```

## LongRunningTool.cs

```csharp
using ModelContextProtocol;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;
using System.ComponentModel;

namespace EverythingServer.Tools;

[McpServerToolType]
public class LongRunningTool
{
    [McpServerTool(Name = "longRunningOperation"), Description("Demonstrates a long running operation with progress updates")]
    public static async Task<string> LongRunningOperation(
        IMcpServer server,
        RequestContext<CallToolRequestParams> context,
        int duration = 10,
        int steps = 5)
    {
        var progressToken = context.Params?.Meta?.ProgressToken;
        var stepDuration = duration / steps;

        for (int i = 1; i <= steps + 1; i++)
        {
            await Task.Delay(stepDuration * 1000);
            
            if (progressToken is not null)
            {
                await server.SendNotificationAsync("notifications/progress", new
                    {
                        Progress = i,
                        Total = steps,
                        progressToken
                    });
            }
        }

        return $"Long running operation completed. Duration: {duration} seconds. Steps: {steps}.";
    }
}
```

## SampleLlmTool.cs

```csharp
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;
using System.ComponentModel;

namespace EverythingServer.Tools;

[McpServerToolType]
public class SampleLlmTool
{
    [McpServerTool(Name = "sampleLLM"), Description("Samples from an LLM using MCP's sampling feature")]
    public static async Task<string> SampleLLM(
        IMcpServer server,
        [Description("The prompt to send to the LLM")] string prompt,
        [Description("Maximum number of tokens to generate")] int maxTokens,
        CancellationToken cancellationToken)
    {
        var samplingParams = CreateRequestSamplingParams(prompt ?? string.Empty, "sampleLLM", maxTokens);
        var sampleResult = await server.RequestSamplingAsync(samplingParams, cancellationToken);

        return $"LLM sampling result: {sampleResult.Content.Text}";
    }

    private static CreateMessageRequestParams CreateRequestSamplingParams(string context, string uri, int maxTokens = 100)
    {
        return new CreateMessageRequestParams()
        {
            Messages = [new SamplingMessage()
                {
                    Role = Role.User,
                    Content = new Content()
                    {
                        Type = "text",
                        Text = $"Resource {uri} context: {context}"
                    }
                }],
            SystemPrompt = "You are a helpful test server.",
            MaxTokens = maxTokens,
            Temperature = 0.7f,
            IncludeContext = ContextInclusion.ThisServer
        };
    }
}
```
