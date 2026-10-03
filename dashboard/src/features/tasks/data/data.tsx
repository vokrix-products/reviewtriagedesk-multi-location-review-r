import {Clock, TriangleAlert, CircleCheckBig} from 'lucide-react'

export const labels = [
  {
    value: 'bug',
    label: 'Bug',
  },
  {
    value: 'feature',
    label: 'Feature',
  },
  {
    value: 'documentation',
    label: 'Documentation',
  },
]

// Severity tiers drive badge color. Every status maps to exactly one tier:
//   critical -> red (destructive)   e.g. expired, denied, failed
//   warning  -> amber (warning)     e.g. expiring soon, needs review
//   good     -> green (success)     e.g. valid, approved, done
//   neutral  -> gray (secondary)    e.g. pending, queued, n/a
export type Severity = 'critical' | 'warning' | 'good' | 'neutral' | 'info'

export const severityToBadgeVariant: Record<Severity, 'destructive' | 'warning' | 'success' | 'secondary'> = {
  critical: 'destructive',
  warning: 'warning',
  good: 'success',
  neutral: 'secondary',
  info: 'secondary',
}

// PRODUCT_CUSTOMIZE: replace this list with the real statuses this product
// produces (must match exactly what the backend poller writes to
// records.status). Every status must declare a severity tier above. Default
// values below are generic placeholders only — do not ship as-is.
// __STATUSES_BLOCK_START__
export const statuses: {
  label: string
  value: string
  icon: typeof TriangleAlert
  severity: Severity
}[] = [
  { label: 'New', value: 'new:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Unread', value: 'unread:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Unresponded', value: 'unresponded:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Draft Pending', value: 'draft_pending:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Draft Generated', value: 'draft_generated:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Needs Approval', value: 'needs_approval:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Approved', value: 'approved:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Posted', value: 'posted:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Skipped', value: 'skipped:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Snoozed', value: 'snoozed:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Reopened', value: 'reopened:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Archived', value: 'archived:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Failed Post', value: 'failed_post:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Flagged', value: 'flagged:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Sensitive', value: 'sensitive:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Legal Hold', value: 'legal_hold:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Refund Risk', value: 'refund_risk:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Safety Risk', value: 'safety_risk:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Health Risk', value: 'health_risk:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Discrimination Risk', value: 'discrimination_risk:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Churn Risk', value: 'churn_risk:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Escalation Required', value: 'escalation_required:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Approval Required', value: 'approval_required:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Auto Post Eligible', value: 'auto_post_eligible:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Auto Post Blocked', value: 'auto_post_blocked:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Sla Ok', value: 'sla_ok:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Sla At Risk', value: 'sla_at_risk:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Sla Breached', value: 'sla_breached:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Sla Paused Business Hours', value: 'sla_paused_business_hours:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Unassigned', value: 'unassigned:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Assigned', value: 'assigned:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Escalated', value: 'escalated:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Awaiting Approval', value: 'awaiting_approval:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Approved By Hq', value: 'approved_by_hq:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Approved By Region', value: 'approved_by_region:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Approved By Location', value: 'approved_by_location:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Matched', value: 'matched:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Ambiguous', value: 'ambiguous:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Misrouted', value: 'misrouted:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Missing Location', value: 'missing_location:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Duplicate', value: 'duplicate:info', icon: Clock, severity: 'info' as Severity },
  { label: 'Source Unmapped', value: 'source_unmapped:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Connected', value: 'connected:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Token Expired', value: 'token_expired:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Sync Error', value: 'sync_error:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Source Disconnected', value: 'source_disconnected:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'No Review Access', value: 'no_review_access:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Pending Authorization', value: 'pending_authorization:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Brand Voice Missing', value: 'brand_voice_missing:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Location Voice Missing', value: 'location_voice_missing:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Template Missing', value: 'template_missing:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Policy Conflict', value: 'policy_conflict:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Compliance Review', value: 'compliance_review:warning', icon: Clock, severity: 'warning' as Severity },
  { label: 'Missing', value: 'missing:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Expired', value: 'expired:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Valid', value: 'valid:good', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Parse Error', value: 'parse_error:critical', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Duplicate Row', value: 'duplicate_row:warning', icon: Clock, severity: 'warning' as Severity },
]
// __STATUSES_BLOCK_END__
