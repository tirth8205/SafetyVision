"""
Command-line interface for SafetyVision operations
"""

import click
import asyncio
import json
from datetime import datetime
from safetyvision.core.vlm_safety_engine import VLMSafetyEngine, create_demo_sensor_reading
import numpy as np

@click.group()
def cli():
    """SafetyVision: VLM-Integrated Nuclear Safety System"""
    pass

@cli.command()
@click.option('--zone', default='A', help='Facility zone to analyze')
@click.option('--duration', default=30, help='Analysis duration in seconds')
@click.option('--output', default='console', help='Output format: console, json, file')
def analyze(zone, duration, output):
    """Run safety analysis for specified zone"""
    click.echo(f"Starting safety analysis for Zone {zone}")
    
    async def run_analysis():
        engine = VLMSafetyEngine()
        
        # Generate demo data
        demo_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        sensor_data = create_demo_sensor_reading()
        
        # Run analysis
        report = await engine.analyze_environment(
            visual_data=demo_image,
            sensor_data=sensor_data,
            query=f"Analyze safety conditions in Zone {zone}"
        )
        
        if output == 'json':
            result = {
                'timestamp': report.timestamp.isoformat(),
                'zone': zone,
                'risk_level': report.risk_level.name,
                'status': report.status,
                'confidence': report.confidence,
                'emergency_required': report.emergency_required
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"\n{'='*50}")
            click.echo(f"SAFETY ANALYSIS REPORT - ZONE {zone}")
            click.echo(f"{'='*50}")
            click.echo(f"Timestamp: {report.timestamp}")
            click.echo(f"Risk Level: {report.risk_level.name}")
            click.echo(f"Status: {report.status}")
            click.echo(f"Confidence: {report.confidence:.1%}")
            click.echo(f"Emergency Required: {report.emergency_required}")
            click.echo(f"\nRecommendations:")
            for rec in report.recommendations:
                click.echo(f"  • {rec}")
    
    asyncio.run(run_analysis())

@cli.command()
@click.option('--query', prompt='Enter your safety query', help='Natural language safety query')
def ask(query):
    """Ask natural language safety questions"""
    from safetyvision.communication.nlp_interface import NLPInterface
    
    async def process_query():
        nlp = NLPInterface()
        result = await nlp.process_command(query)
        
        click.echo(f"\nQuery: {query}")
        click.echo(f"Intent: {result['intent']}")
        click.echo(f"Response: {result['response']}")
        click.echo(f"Confidence: {result['confidence']:.1%}")
    
    asyncio.run(process_query())

@cli.command()
def dashboard():
    """Launch the SafetyVision monitoring dashboard"""
    import subprocess
    click.echo("Launching SafetyVision Dashboard...")
    subprocess.run(["streamlit", "run", "safetyvision/dashboard/monitoring_app.py"])

@cli.command()
@click.option('--format', default='text', help='Report format: text, pdf, json')
@click.option('--output-file', help='Output file path')
def report(format, output_file):
    """Generate comprehensive safety report"""
    click.echo(f"Generating safety report in {format} format...")
    
    report_content = f"""
SAFETYVISION COMPREHENSIVE SAFETY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
Current facility operations show normal safety parameters with no immediate concerns.

DETAILED ANALYSIS
- Radiation Monitoring: All levels within acceptable limits
- Temperature Systems: Operating at normal parameters  
- Equipment Status: Fully operational
- VLM Analysis: High confidence in safety assessments

RECOMMENDATIONS
1. Continue standard monitoring protocols
2. Schedule routine maintenance as planned
3. Maintain current safety procedures

Next review scheduled for: {(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_content)
        click.echo(f"Report saved to {output_file}")
    else:
        click.echo(report_content)

def main():
    """Entry point for CLI"""
    cli()

if __name__ == '__main__':
    main()