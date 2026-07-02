// Import user types for local use
import type { PublicUser } from "./user";

// Re-export user types
export type {
  User,
  PublicUser,
  AuthResponse,
  LoginInput,
  RegisterInput,
} from "./user";

// Q&A types
export interface Tag {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  color: string;
  usage_count: number;
  created_at: string;
}

export interface Question {
  id: string;
  title: string;
  body: string;
  body_html?: string;
  author_id: string;
  author: PublicUser | null;
  tags: Tag[];
  vote_count: number;
  answer_count: number;
  view_count: number;
  accepted_answer_id: string | null;
  is_closed: boolean;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuestionListResult {
  questions: Question[];
  total: number;
  page: number;
  pages: number;
}

export interface QuestionCreateInput {
  title: string;
  body: string;
  tag_ids?: string[];
}

export interface QuestionUpdateInput {
  title?: string;
  body?: string;
  tag_ids?: string[];
}

export interface Answer {
  id: string;
  question_id: string;
  author_id: string;
  author: PublicUser | null;
  body: string;
  body_html?: string;
  vote_count: number;
  is_accepted: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnswerListResult {
  answers: Answer[];
  total: number;
  page: number;
  pages: number;
}

export interface AnswerCreateInput {
  question_id: string;
  body: string;
}

export interface VoteCreateInput {
  vote_type: "up" | "down";
  target_type: "question" | "answer";
  target_id: string;
}

export interface Comment {
  id: string;
  user_id: string;
  user: PublicUser | null;
  body: string;
  target_type: string;
  target_id: string;
  created_at: string;
  updated_at: string;
}

export interface CommentListResult {
  comments: Comment[];
  total: number;
  page: number;
  pages: number;
}

export interface CommentCreateInput {
  body: string;
  target_type: "question" | "answer" | "issue";
  target_id: string;
}

export interface Bookmark {
  id: string;
  user_id: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

export interface BookmarkListResult {
  bookmarks: Bookmark[];
  total: number;
  page: number;
  pages: number;
}

export interface TagListResult {
  tags: Tag[];
  total: number;
  page: number;
  pages: number;
}

// -- Project management types --

export interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  owner: PublicUser | null;
  visibility: "public" | "private";
  star_count: number;
  starred?: boolean;
  members_count: number;
  issues_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResult {
  projects: Project[];
  total: number;
  page: number;
  pages: number;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  user: PublicUser | null;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

export interface Issue {
  id: string;
  project_id: string;
  issue_number: number;
  title: string;
  body: string | null;
  body_html: string | null;
  author_id: string;
  author: PublicUser | null;
  assignee_id: string | null;
  assignee: PublicUser | null;
  status: "open" | "in_progress" | "closed";
  priority: "low" | "medium" | "high" | "critical";
  milestone_id: string | null;
  milestone: Milestone | null;
  tags?: Tag[];
  /** 预估工时（秒），null 表示未估时 */
  time_estimate: number | null;
  /** 已耗时（秒），反范式聚合缓存 */
  time_spent: number;
  created_at: string;
  updated_at: string;
}

/** Issue 耗时记录条目。seconds 为本次记录的耗时（秒）。 */
export interface TimeEntry {
  id: string;
  issue_id: string;
  user_id: string;
  user: PublicUser | null;
  seconds: number;
  note: string | null;
  created_at: string;
}

/** GET time-entries 端点返回结构。 */
export interface TimeEntryListResult {
  time_entries: TimeEntry[];
  total: number;
}

export interface IssueListResult {
  issues: Issue[];
  stats: { open: number; in_progress: number; closed: number; total: number };
  total: number;
  page: number;
  pages: number;
}

export interface Milestone {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  status: "open" | "closed";
  open_issues: number;
  closed_issues: number;
  created_at: string;
  updated_at: string;
}

export interface KanbanColumn {
  id: string;
  project_id: string;
  title: string;
  position: number;
  cards?: KanbanCard[];
  created_at: string;
}

export interface KanbanCard {
  id: string;
  column_id: string;
  issue_id: string | null;
  issue: Issue | null;
  title: string;
  position: number;
  created_at: string;
}

// -- Search types --

export interface SearchResult {
  items: SearchResultItem[];
  total: number;
  page: number;
  pages: number;
}

export interface SearchResultItem {
  doc_id: string;
  source_type: "question" | "answer" | "issue" | "project";
  title: string;
  body_text: string;
  tags: string[];
  created_at: string;
  extra: Record<string, unknown>;
}

// -- Notification types --

export interface Notification {
  id: string;
  recipient_id: string;
  type: string;
  title: string;
  body: string | null;
  link: string | null;
  source_type: string | null;
  source_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResult {
  items: Notification[];
  total: number;
  page: number;
  pages: number;
}

// -- User profile types --

export interface UserProfile {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  website: string | null;
  location: string | null;
  reputation: number;
  role: string;
  created_at: string;
  stats?: {
    questions: number;
    answers: number;
    projects: number;
  };
}

// -- Badge types --

export interface Badge {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string;
  kind: string;
  created_at: string;
  updated_at: string;
}

export interface BadgeCreateInput {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface BadgeUpdateInput {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface UserBadge {
  id: string;
  user_id: string;
  badge_id: string;
  badge: Badge | null;
  awarded_by: string | null;
  reason: string | null;
  created_at: string;
}
