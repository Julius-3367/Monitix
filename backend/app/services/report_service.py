"""Report generation service."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json
from pathlib import Path

from app.db.models import Report, Server, Alert, MetricData

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating reports."""
    
    @staticmethod
    def generate_report(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        report_type: str = "periodic",
        user_id: Optional[int] = None
    ) -> Report:
        """Generate a comprehensive report."""
        logger.info(f"Generating report for period {start_time} to {end_time}")
        
        # Create report record
        report = Report(
            report_type=report_type,
            period_start=start_time,
            period_end=end_time,
            generated_by=user_id,
            status="generating"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        try:
            # Collect data
            summary = ReportService._collect_report_data(db, start_time, end_time)
            
            # Update report
            report.summary = summary
            report.status = "completed"
            
            # Generate file (HTML for now)
            file_path = ReportService._generate_html_report(report, summary)
            report.file_path = file_path
            report.file_format = "html"
            
            db.commit()
            db.refresh(report)
            
            logger.info(f"Report generated successfully: {report.id}")
            return report
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            report.status = "failed"
            db.commit()
            raise
    
    @staticmethod
    def _collect_report_data(db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Collect all data for the report."""
        # Get all active servers
        servers = db.query(Server).filter(Server.is_active == True).all()
        
        # Get alerts in period
        alerts = db.query(Alert).filter(
            Alert.triggered_at >= start_time,
            Alert.triggered_at <= end_time
        ).all()
        
        # Server statistics
        server_stats = []
        total_cpu = 0
        total_memory = 0
        servers_online = 0
        servers_offline = 0
        
        for server in servers:
            # Get metrics for this period
            metrics = db.query(MetricData).filter(
                MetricData.server_id == server.id,
                MetricData.timestamp >= start_time,
                MetricData.timestamp <= end_time
            ).all()
            
            if metrics:
                # Calculate averages
                avg_cpu = sum(m.cpu_usage_percent for m in metrics if m.cpu_usage_percent) / len(metrics)
                avg_memory = sum(m.memory_percent for m in metrics if m.memory_percent) / len(metrics)
                max_cpu = max((m.cpu_usage_percent for m in metrics if m.cpu_usage_percent), default=0)
                max_memory = max((m.memory_percent for m in metrics if m.memory_percent), default=0)
                
                # Max disk usage
                max_disk = 0
                for m in metrics:
                    if m.disk_usage:
                        for disk in m.disk_usage:
                            if disk.get('percent', 0) > max_disk:
                                max_disk = disk['percent']
                
                total_cpu += avg_cpu
                total_memory += avg_memory
                
                server_stats.append({
                    'hostname': server.hostname,
                    'status': server.status,
                    'avg_cpu': round(avg_cpu, 2),
                    'avg_memory': round(avg_memory, 2),
                    'max_cpu': round(max_cpu, 2),
                    'max_memory': round(max_memory, 2),
                    'max_disk': round(max_disk, 2),
                    'alert_count': len([a for a in alerts if a.server_id == server.id])
                })
                
                if server.status == 'online':
                    servers_online += 1
                else:
                    servers_offline += 1
            else:
                server_stats.append({
                    'hostname': server.hostname,
                    'status': 'no_data',
                    'avg_cpu': 0,
                    'avg_memory': 0,
                    'max_cpu': 0,
                    'max_memory': 0,
                    'max_disk': 0,
                    'alert_count': 0
                })
                servers_offline += 1
        
        # Alert statistics
        alert_critical = len([a for a in alerts if a.severity == 'critical'])
        alert_warning = len([a for a in alerts if a.severity == 'warning'])
        alert_resolved = len([a for a in alerts if a.resolved_at])
        
        # System health score (0-100)
        health_score = 100
        health_score -= (servers_offline * 5)  # -5 per offline server
        health_score -= (alert_critical * 10)  # -10 per critical alert
        health_score -= (alert_warning * 2)    # -2 per warning alert
        health_score = max(0, health_score)
        
        return {
            'period_start': start_time.isoformat(),
            'period_end': end_time.isoformat(),
            'total_servers': len(servers),
            'servers_online': servers_online,
            'servers_offline': servers_offline,
            'total_alerts': len(alerts),
            'alert_critical': alert_critical,
            'alert_warning': alert_warning,
            'alert_resolved': alert_resolved,
            'system_health_score': health_score,
            'avg_cpu_all_servers': round(total_cpu / len(servers), 2) if servers else 0,
            'avg_memory_all_servers': round(total_memory / len(servers), 2) if servers else 0,
            'server_stats': sorted(server_stats, key=lambda x: x.get('avg_cpu', 0), reverse=True),
            'top_issues': ReportService._get_top_issues(server_stats, alerts)
        }
    
    @staticmethod
    def _get_top_issues(server_stats: List[Dict], alerts: List[Alert]) -> List[str]:
        """Get top 3 issues/concerns."""
        issues = []
        
        # High CPU servers
        high_cpu = [s for s in server_stats if s.get('avg_cpu', 0) > 80]
        if high_cpu:
            issues.append(f"{len(high_cpu)} server(s) with high CPU usage")
        
        # High memory servers
        high_mem = [s for s in server_stats if s.get('avg_memory', 0) > 80]
        if high_mem:
            issues.append(f"{len(high_mem)} server(s) with high memory usage")
        
        # Critical alerts
        critical = [a for a in alerts if a.severity == 'critical' and not a.resolved_at]
        if critical:
            issues.append(f"{len(critical)} unresolved critical alert(s)")
        
        # Offline servers
        offline = [s for s in server_stats if s.get('status') != 'online']
        if offline:
            issues.append(f"{len(offline)} server(s) offline or unreachable")
        
        return issues[:3]
    
    @staticmethod
    def _generate_html_report(report: Report, summary: Dict[str, Any]) -> str:
        """Generate HTML report file."""
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.id}_{timestamp}.html"
        file_path = reports_dir / filename
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Report - {summary['period_start']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2563eb; }}
        .summary {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .stat {{ display: inline-block; margin: 10px 20px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ color: #6b7280; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f3f4f6; font-weight: bold; }}
        .status-online {{ color: #10b981; }}
        .status-offline {{ color: #ef4444; }}
        .severity-critical {{ color: #ef4444; font-weight: bold; }}
        .severity-warning {{ color: #f59e0b; }}
    </style>
</head>
<body>
    <h1>Server Monitoring Report</h1>
    <p>Period: {summary['period_start']} to {summary['period_end']}</p>
    <p>Generated: {datetime.utcnow().isoformat()}</p>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="stat">
            <div class="stat-value">{summary['total_servers']}</div>
            <div class="stat-label">Total Servers</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #10b981">{summary['servers_online']}</div>
            <div class="stat-label">Online</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #ef4444">{summary['servers_offline']}</div>
            <div class="stat-label">Offline</div>
        </div>
        <div class="stat">
            <div class="stat-value">{summary['total_alerts']}</div>
            <div class="stat-label">Total Alerts</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #2563eb">{summary['system_health_score']}</div>
            <div class="stat-label">Health Score</div>
        </div>
    </div>
    
    <h2>Top Issues</h2>
    <ul>
        {''.join(f'<li>{issue}</li>' for issue in summary['top_issues']) if summary['top_issues'] else '<li>No major issues detected</li>'}
    </ul>
    
    <h2>Server Performance</h2>
    <table>
        <thead>
            <tr>
                <th>Hostname</th>
                <th>Status</th>
                <th>Avg CPU %</th>
                <th>Max CPU %</th>
                <th>Avg Memory %</th>
                <th>Max Memory %</th>
                <th>Max Disk %</th>
                <th>Alerts</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f'''
            <tr>
                <td>{s['hostname']}</td>
                <td class="status-{s['status']}">{s['status']}</td>
                <td>{s['avg_cpu']}</td>
                <td>{s['max_cpu']}</td>
                <td>{s['avg_memory']}</td>
                <td>{s['max_memory']}</td>
                <td>{s['max_disk']}</td>
                <td>{s['alert_count']}</td>
            </tr>
            ''' for s in summary['server_stats'])}
        </tbody>
    </table>
</body>
</html>
        """
        
        # Write file
        with open(file_path, 'w') as f:
            f.write(html)
        
        return str(file_path)
    
    @staticmethod
    def get_latest_report(db: Session) -> Optional[Report]:
        """Get the latest completed report."""
        return db.query(Report).filter(
            Report.status == "completed"
        ).order_by(Report.generated_at.desc()).first()
