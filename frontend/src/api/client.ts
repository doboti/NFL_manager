import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type Tactic = "BALANCED" | "PASS_HEAVY" | "RUN_HEAVY" | "BLITZ" | "PREVENT";
export type SponsorType = "FIXED" | "PERFORMANCE";
export type TradeStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "CANCELLED";

export interface Player {
  id: number;
  team_id: number | null;
  first_name: string;
  last_name: string;
  position: string;
  age: number;
  overall: number;
  xp: number;
  xp_to_next_level: number;
  market_price: number | null;
  photo_url: string | null;
  nfl_team: string | null;
  listed_for_transfer: boolean;
  asking_price: number | null;
  is_starter: boolean;
}

export interface Team {
  id: number;
  name: string;
  nfl_team_code: string | null;
  franchise_capital: number;
  stadium_level: number;
  tactic: Tactic;
  wins: number;
  losses: number;
  ties: number;
  created_at: string;
  next_match_at: string;
  players: Player[];
}

export interface TeamStanding {
  id: number;
  name: string;
  nfl_team_code: string | null;
  is_bot: boolean;
  wins: number;
  losses: number;
  ties: number;
  avg_overall: number | null;
}

export interface DivisionStandings {
  conference: string;
  division: string;
  teams: TeamStanding[];
}

export interface SeasonStatus {
  season: number;
  phase: "REGULAR" | "PLAYOFFS";
  season_day: number;
  regular_season_days: number;
  current_playoff_round: string | null;
}

export interface ScheduledMatch {
  id: number;
  home_team_id: number;
  away_team_id: number;
  home_team_name: string;
  away_team_name: string;
  scheduled_at: string;
  is_playoff: boolean;
  playoff_round: string | null;
}

export interface TeamSummary {
  id: number;
  name: string;
  nfl_team_code: string | null;
  is_bot: boolean;
  avg_overall: number | null;
}

export interface TeamRoster {
  id: number;
  name: string;
  nfl_team_code: string | null;
  players: Player[];
}

export interface NFLTeamOption {
  code: string;
  name: string;
  taken: boolean;
  controlled_by_bot: boolean;
}

export interface TrainingSession {
  id: number;
  player_id: number;
  started_at: string;
  ends_at: string;
  xp_awarded: number;
  completed: boolean;
  collected: boolean;
}

export interface StadiumUpgrade {
  id: number;
  target_level: number;
  started_at: string;
  ends_at: string;
  collected: boolean;
}

export interface SponsorTemplate {
  key: string;
  name: string;
  sponsor_type: SponsorType;
  daily_amount: number;
  win_bonus: number;
  duration_days: number;
}

export interface Sponsor {
  id: number;
  template_key: string;
  name: string;
  sponsor_type: SponsorType;
  daily_amount: number;
  win_bonus: number;
  signed_at: string;
  expires_at: string;
}

export interface Match {
  id: number;
  home_team_id: number;
  away_team_id: number;
  home_team_name: string;
  away_team_name: string;
  home_score: number | null;
  away_score: number | null;
  home_tactic: Tactic;
  away_tactic: Tactic;
  play_log: string[] | null;
  played: boolean;
  played_at: string | null;
  is_playoff: boolean;
  playoff_round: string | null;
}

export interface PracticeMatchResult {
  opponent_name: string;
  home_score: number;
  away_score: number;
  play_log: string[];
}

export interface TradeOffer {
  id: number;
  from_team_id: number;
  to_team_id: number;
  from_team_name: string;
  to_team_name: string;
  target_player: Player;
  offered_player: Player | null;
  cash_offer: number;
  status: TradeStatus;
  created_at: string;
  resolved_at: string | null;
}

// --- auth & team selection ---

export async function register(email: string, password: string, displayName: string) {
  const { data } = await apiClient.post<{ access_token: string }>("/auth/register", {
    email,
    password,
    display_name: displayName,
  });
  return data.access_token;
}

export async function login(email: string, password: string) {
  const { data } = await apiClient.post<{ access_token: string }>("/auth/login", {
    email,
    password,
  });
  return data.access_token;
}

export interface CurrentUser {
  id: number;
  email: string;
  display_name: string;
  is_admin: boolean;
}

export async function fetchCurrentUser() {
  const { data } = await apiClient.get<CurrentUser>("/auth/me");
  return data;
}

export async function listAvailableTeams() {
  const { data } = await apiClient.get<NFLTeamOption[]>("/teams/available");
  return data;
}

export async function claimTeam(nflTeamCode: string) {
  const { data } = await apiClient.post<Team>("/teams/claim", { nfl_team_code: nflTeamCode });
  return data;
}

export async function releaseTeam() {
  await apiClient.post("/teams/release");
}

export async function fetchMyTeam() {
  const { data } = await apiClient.get<Team>("/teams/me");
  return data;
}

export async function setTeamTactic(tactic: Tactic) {
  const { data } = await apiClient.put<Team>("/teams/tactic", { tactic });
  return data;
}

export async function listOtherTeams() {
  const { data } = await apiClient.get<TeamSummary[]>("/teams/");
  return data;
}

export async function fetchTeamRoster(teamId: number) {
  const { data } = await apiClient.get<TeamRoster>(`/teams/${teamId}/roster`);
  return data;
}

// --- stadium (timed upgrade) ---

export async function getStadiumUpgrade() {
  const { data } = await apiClient.get<StadiumUpgrade | null>("/stadium/upgrade");
  return data;
}

export async function startStadiumUpgrade() {
  const { data } = await apiClient.post<StadiumUpgrade>("/stadium/upgrade/start");
  return data;
}

export async function collectStadiumUpgrade() {
  const { data } = await apiClient.post<StadiumUpgrade>("/stadium/upgrade/collect");
  return data;
}

// --- training ---

export async function listTraining() {
  const { data } = await apiClient.get<TrainingSession[]>("/training/");
  return data;
}

export async function startTraining(playerId: number) {
  const { data } = await apiClient.post<TrainingSession>("/training/start", { player_id: playerId });
  return data;
}

export async function collectTraining(sessionId: number) {
  const { data } = await apiClient.post<TrainingSession>(`/training/${sessionId}/collect`);
  return data;
}

// --- sponsors ---

export async function listSponsors() {
  const { data } = await apiClient.get<Sponsor[]>("/sponsors/");
  return data;
}

export async function getSponsorTemplates() {
  const { data } = await apiClient.get<SponsorTemplate[]>("/sponsors/templates");
  return data;
}

export async function signSponsor(templateKey: string) {
  const { data } = await apiClient.post<Sponsor>("/sponsors/sign", { template_key: templateKey });
  return data;
}

// --- matches ---

export async function listMatches() {
  const { data } = await apiClient.get<Match[]>("/matches/");
  return data;
}

export async function playPracticeMatch() {
  const { data } = await apiClient.post<PracticeMatchResult>("/matches/practice");
  return data;
}

export async function getUpcomingMatch() {
  const { data } = await apiClient.get<ScheduledMatch | null>("/matches/upcoming");
  return data;
}

// --- league: standings & schedule ---

export async function getStandings() {
  const { data } = await apiClient.get<DivisionStandings[]>("/league/standings");
  return data;
}

export async function getSeasonStatus() {
  const { data } = await apiClient.get<SeasonStatus>("/league/season");
  return data;
}

export async function getLeagueSchedule(limit = 30) {
  const { data } = await apiClient.get<ScheduledMatch[]>("/league/schedule", { params: { limit } });
  return data;
}

export interface SeasonHistoryEntry {
  season: number;
  wins: number;
  losses: number;
  ties: number;
  playoff_result: string;
}

export async function getSeasonHistory() {
  const { data } = await apiClient.get<SeasonHistoryEntry[]>("/teams/me/history");
  return data;
}

// --- starting lineup ---

export async function getLineup() {
  const { data } = await apiClient.get<Player[]>("/roster/lineup");
  return data;
}

export async function setLineup(
  qbId: number,
  rbIds: number[],
  wrIds: number[],
  teId: number,
  defId: number
) {
  const { data } = await apiClient.put<Player[]>("/roster/lineup", {
    qb_id: qbId,
    rb_ids: rbIds,
    wr_ids: wrIds,
    te_id: teId,
    def_id: defId,
  });
  return data;
}

// --- free agent market ---

export interface MarketFilters {
  position?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface MarketPage {
  players: Player[];
  total: number;
}

export async function listMarket(filters: MarketFilters = {}): Promise<MarketPage> {
  const { data, headers } = await apiClient.get<Player[]>("/market/", { params: filters });
  return { players: data, total: Number(headers["x-total-count"] ?? data.length) };
}

export async function buyPlayer(playerId: number) {
  const { data } = await apiClient.post<Team>(`/market/${playerId}/buy`);
  return data;
}

// --- roster management: release & transfer listing ---

export async function releasePlayer(playerId: number) {
  const { data } = await apiClient.post<Player>(`/roster/${playerId}/release`);
  return data;
}

export async function listPlayerForTransfer(playerId: number, askingPrice: number) {
  const { data } = await apiClient.post<Player>(`/roster/${playerId}/list-for-transfer`, {
    asking_price: askingPrice,
  });
  return data;
}

export async function unlistPlayerFromTransfer(playerId: number) {
  const { data } = await apiClient.post<Player>(`/roster/${playerId}/unlist`);
  return data;
}

export async function listTransferMarket() {
  const { data } = await apiClient.get<Player[]>("/transfers/");
  return data;
}

export async function buyTransferListedPlayer(playerId: number) {
  const { data } = await apiClient.post<Team>(`/transfers/${playerId}/buy`);
  return data;
}

// --- trades / negotiations ---

export async function listTradeOffers() {
  const { data } = await apiClient.get<TradeOffer[]>("/trades/");
  return data;
}

export async function createTradeOffer(
  toTeamId: number,
  targetPlayerId: number,
  offeredPlayerId: number | null,
  cashOffer: number
) {
  const { data } = await apiClient.post<TradeOffer>("/trades/offer", {
    to_team_id: toTeamId,
    target_player_id: targetPlayerId,
    offered_player_id: offeredPlayerId,
    cash_offer: cashOffer,
  });
  return data;
}

export async function acceptTradeOffer(offerId: number) {
  const { data } = await apiClient.post<TradeOffer>(`/trades/${offerId}/accept`);
  return data;
}

export async function rejectTradeOffer(offerId: number) {
  const { data } = await apiClient.post<TradeOffer>(`/trades/${offerId}/reject`);
  return data;
}

export async function cancelTradeOffer(offerId: number) {
  const { data } = await apiClient.post<TradeOffer>(`/trades/${offerId}/cancel`);
  return data;
}

// --- admin / dev-only virtual clock ---

export interface TimeStatus {
  offset_seconds: number;
  virtual_now: string;
}

export interface AdvanceTimeResponse {
  time: TimeStatus;
  daily_cycle: Record<string, unknown> | null;
}

export async function getTimeStatus() {
  const { data } = await apiClient.get<TimeStatus>("/admin/time");
  return data;
}

export async function advanceTime(hours: number) {
  const { data } = await apiClient.post<AdvanceTimeResponse>("/admin/advance-time", { hours });
  return data;
}

export async function resetTime() {
  const { data } = await apiClient.post<TimeStatus>("/admin/reset-time");
  return data;
}

export interface AdminUser {
  id: number;
  email: string;
  display_name: string;
  is_bot: boolean;
  is_admin: boolean;
  team_name: string | null;
}

export async function listAdminUsers() {
  const { data } = await apiClient.get<AdminUser[]>("/admin/users");
  return data;
}

export async function deleteAdminUser(userId: number) {
  await apiClient.delete(`/admin/users/${userId}`);
}
