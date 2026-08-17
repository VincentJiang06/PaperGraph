# Public interfaces — `src/paperproof` (v1)

Derived from code (reorganize-logic rebuild). One row per public top-level
`def`/`class` (gate-extracted surface). `Source` is relative to the project root.

## Public interface

| Symbol | Signature | Source |
|---|---|---|
| **— Package root & shared utilities —** | | |
| `now` | `now() -> str` | `src/paperproof/clock.py:14` |
| `actor` | `actor(explicit: str \| None = None) -> str` | `src/paperproof/clock.py:22` |
| `PaperproofError` | `class PaperproofError(Exception); exit_code=1; __init__(self, errors: list[str] \| None = None, *, data: dict[str, Any] \| None = None, warnings: list[str] \| None = None, message: str \| None = None) -> None` | `src/paperproof/errors.py:14` |
| `DomainError` | `class DomainError(PaperproofError); exit_code=1` | `src/paperproof/errors.py:33` |
| `UsageError` | `class UsageError(PaperproofError); exit_code=2` | `src/paperproof/errors.py:39` |
| `CorruptStateError` | `class CorruptStateError(PaperproofError); exit_code=3` | `src/paperproof/errors.py:45` |
| `next_id` | `next_id(prefix: str, existing: Iterable[str], width: int \| None = None) -> str` | `src/paperproof/ids.py:56` |
| `node_id` | `node_id(existing_node_ids: Iterable[str]) -> str` | `src/paperproof/ids.py:62` |
| `edge_id` | `edge_id(source_node_id: str, target_node_id: str, edge_type: str, existing_edge_ids: Iterable[str]) -> str` | `src/paperproof/ids.py:75` |
| `bundle_id` | `bundle_id(kind: str, target_id: str, revision: int = 1) -> str` | `src/paperproof/ids.py:108` |
| `next_bundle_revision` | `next_bundle_revision(kind: str, target_id: str, existing_ids: Iterable[str]) -> int` | `src/paperproof/ids.py:122` |
| `Paths` | `@dataclass(frozen=True) class Paths{root: Path, project_id: str}; props: project_dir, paper_spec, project_contract, snapshots; methods: resolve(relpath: str) -> Path, exists() -> bool` | `src/paperproof/paths.py:82` |
| `paths_for` | `paths_for(root: str \| Path, project_id: str) -> Paths` | `src/paperproof/paths.py:111` |
| `init` | `init(paths: Paths) -> dict[str, Any]` | `src/paperproof/project.py:18` |
| `status` | `status(paths: Paths) -> dict[str, Any]` | `src/paperproof/project.py:40` |
| `to_canonical_obj` | `to_canonical_obj(obj: Any) -> Any` | `src/paperproof/serialize.py:16` |
| `canonical_line` | `canonical_line(obj: Any) -> str` | `src/paperproof/serialize.py:27` |
| `canonical_bytes` | `canonical_bytes(obj: Any) -> bytes` | `src/paperproof/serialize.py:33` |
| `normalize` | `normalize(s: str) -> str` | `src/paperproof/textutil.py:33` |
| `casefold` | `casefold(s: str) -> str` | `src/paperproof/textutil.py:40` |
| `is_cjk` | `is_cjk(ch: str) -> bool` | `src/paperproof/textutil.py:45` |
| `tokens` | `tokens(s: str) -> list[str]` | `src/paperproof/textutil.py:62` |
| `word_count` | `word_count(s: str) -> int` | `src/paperproof/textutil.py:85` |
| `sentence_split` | `sentence_split(s: str) -> list[str]` | `src/paperproof/textutil.py:96` |
| `sentence_count` | `sentence_count(s: str) -> int` | `src/paperproof/textutil.py:125` |
| `contains` | `contains(hay: str, ndl: str) -> bool` | `src/paperproof/textutil.py:130` |
| `quote_match` | `quote_match(text: str, q: str) -> bool` | `src/paperproof/textutil.py:135` |
| `normalize_dashes` | `normalize_dashes(s: str) -> str` | `src/paperproof/textutil.py:157` |
| `scope_compatible` | `scope_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool` | `src/paperproof/textutil.py:186` |
| `run` | `run(paths: Paths) -> dict[str, Any]` | `src/paperproof/verify.py:272` |
| **— Schemas (pydantic contracts) —** | | |
| `model_for` | `def model_for(schema_version: str) -> type[BaseModel]` | `src/paperproof/schemas/__init__.py:72` |
| `Scope` | `BaseModel(STRICT){period:Optional[str]=None, region:Optional[str]=None, actors:Optional[list[str]]=None, mechanisms:Optional[list[str]]=None} + @model_serializer` | `src/paperproof/schemas/_common.py:16` |
| `AuditFinding` | `BaseModel(STRICT){kind:Literal['binding','strength','scope','coverage'], location:str, target_id:str, detail:str}` | `src/paperproof/schemas/audit.py:12` |
| `AuditReport` | `BaseModel(STRICT){schema_version:Literal['audit_report.v1']='audit_report.v1', audit_id:str, project_id:str, draft_ref:str, findings:list[AuditFinding], passed:bool, created_at:str}` | `src/paperproof/schemas/audit.py:21` |
| `CommitActionEntry` | `BaseModel(STRICT){action:CommitAction, target_id:str, detail:dict[str,Any], record:Optional[dict[str,Any]]=None}` | `src/paperproof/schemas/commit.py:25` |
| `CommitDecision` | `BaseModel(STRICT){schema_version:Literal['commit_decision.v1']='commit_decision.v1', commit_id:str, project_id:str, kind:CommitKind, actor:str, input_ref:str, based_on_snapshot:str, post_snapshot:str, actions:list[CommitActionEntry], created_at:str}` | `src/paperproof/schemas/commit.py:39` |
| `SectionPlanEntry` | `BaseModel(STRICT){section_id:str, role:str, nodes:list[str]}` | `src/paperproof/schemas/compiler.py:17` |
| `Gap` | `BaseModel(STRICT){kind:GapKind, target_id:str, note:str}` | `src/paperproof/schemas/compiler.py:25` |
| `CompilerDryRun` | `BaseModel(STRICT){schema_version:Literal['compiler_dry_run.v1']='compiler_dry_run.v1', run_id:str, project_id:str, snapshot_id:str, writing_ready:bool, section_plan:list[SectionPlanEntry], gaps:list[Gap], created_at:str}` | `src/paperproof/schemas/compiler.py:33` |
| `DraftMapClaim` | `BaseModel(STRICT){node_id:str, claim:str, evidence_ids:list[str], allowed_language:list[str], forbidden_language:list[str]}` | `src/paperproof/schemas/compiler.py:46` |
| `DraftMapSection` | `BaseModel(STRICT){section_id:str, role:str, claims:list[DraftMapClaim], edge_order:list[str]}` | `src/paperproof/schemas/compiler.py:56` |
| `DraftMap` | `BaseModel(STRICT){schema_version:Literal['draft_map.v1']='draft_map.v1', draft_map_id:str, project_id:str, based_on_dry_run:str, sections:list[DraftMapSection], created_at:str}` | `src/paperproof/schemas/compiler.py:65` |
| `DocumentOrigin` | `BaseModel(STRICT){kind:Literal['user_provided','web'], path:Optional[str]=None, url:Optional[str]=None}` | `src/paperproof/schemas/docs.py:34` |
| `Document` | `BaseModel(STRICT){schema_version:Literal['document.v1']='document.v1', doc_id:str, project_id:str, title:str, source_type:SourceType, origin:DocumentOrigin, content_hash:str, text_path:Optional[str], citation_key:str, ingested_from:Optional[str], ingested_at:str}` | `src/paperproof/schemas/docs.py:42` |
| `Provenance` | `BaseModel(STRICT){retrieved_at:str, fetch_method:FetchMethod, tier:Tier, quoted_via:Optional[str]=None}` | `src/paperproof/schemas/docs.py:58` |
| `DocumentV2` | `BaseModel(STRICT){schema_version:Literal['document.v2']='document.v2', doc_id:str, project_id:str, title:str, source_type:SourceType, origin:DocumentOrigin, content_hash:str, text_path:Optional[str], citation_key:str, ingested_from:Optional[str], ingested_at:str, provenance:Provenance}` | `src/paperproof/schemas/docs.py:74` |
| `SourceWorkaround` | `BaseModel(STRICT){kind:WorkaroundKind, note:str}` | `src/paperproof/schemas/docs.py:97` |
| `SourceFetch` | `BaseModel(STRICT){blocked_direct:bool=False, workarounds:list[SourceWorkaround]=[]}` | `src/paperproof/schemas/docs.py:106` |
| `SourceProfile` | `BaseModel(STRICT){schema_version:Literal['source_profile.v1']='source_profile.v1', source_id:str, project_id:str, domain:str, publisher:str='', tier:Tier, fetch:SourceFetch=SourceFetch(), seen_count:int=0, last_ok_fetch_method:Optional[FetchMethod]=None, tier_note:Optional[str]=None, created_at:str}` | `src/paperproof/schemas/docs.py:113` |
| `EvidenceUnit` | `BaseModel(STRICT){schema_version:Literal['evidence_unit.v1']='evidence_unit.v1', evidence_id:str, project_id:str, doc_id:str, location:str, kind:EvidenceKind, quote_or_paraphrase:str, summary:str, support_direction:SupportDirection, can_cite_for:list[str], cannot_cite_for:list[str], scope:Scope, extracted_by:str, ingested_from:Optional[str], created_at:str}` | `src/paperproof/schemas/docs.py:137` |
| `DocsRequest` | `BaseModel(STRICT){schema_version:Literal['docs_request.v1']='docs_request.v1', request_id:str, project_id:str, requested_by:str, target_id:str, need:str, search_hints:list[str], fingerprint:str, status:Literal['open','fulfilled','not_found'], fulfilled_by:Optional[str], created_at:str, fan:bool=False}` | `src/paperproof/schemas/docs.py:157` |
| `DocsResultDocument` | `BaseModel(STRICT){title:str, source_type:SourceType, origin:DocumentOrigin, citation_key:str, text:Optional[str]=None}` | `src/paperproof/schemas/docs.py:176` |
| `DocsResultEvidence` | `BaseModel(STRICT){doc_ref:Optional[int]=None, doc_id:Optional[str]=None, location:str, kind:EvidenceKind, quote_or_paraphrase:str, summary:str, support_direction:SupportDirection, can_cite_for:list[str], cannot_cite_for:list[str], scope:Scope}` | `src/paperproof/schemas/docs.py:186` |
| `DocsResult` | `BaseModel(STRICT){schema_version:Literal['docs_result.v1']='docs_result.v1', request_id:str, project_id:str, documents:list[DocsResultDocument], evidence_units:list[DocsResultEvidence], not_found:bool, search_log:list[str]}` | `src/paperproof/schemas/docs.py:201` |
| `QueryLogEntry` | `BaseModel(STRICT){qid:str, executed:bool, outcome:QueryOutcome, urls_seen:int, docs_taken:int, note:str}` | `src/paperproof/schemas/docs.py:216` |
| `DocsResultV2` | `BaseModel(STRICT){schema_version:Literal['docs_result.v2']='docs_result.v2', request_id:str, project_id:str, documents:list[DocsResultDocument], evidence_units:list[DocsResultEvidence], not_found:bool, query_log:list[QueryLogEntry]}` | `src/paperproof/schemas/docs.py:230` |
| `DocsPack` | `BaseModel(STRICT){schema_version:Literal['docs_pack.v1']='docs_pack.v1', pack_id:str, task_id:str, project_id:str, evidence_units:list[dict], documents_meta:list[dict]}` | `src/paperproof/schemas/docs.py:246` |
| `RetrievalModel` | `BaseModel(STRICT){name:str, revision:str, weights_sha256:str}` | `src/paperproof/schemas/docs.py:260` |
| `RetrievalScore` | `BaseModel(STRICT){evidence_id:str, sscore:str, kscore:str}` | `src/paperproof/schemas/docs.py:271` |
| `RetrievalBlock` | `BaseModel(STRICT_MODEL_OK){matcher:Literal['hybrid.v1','keyword.v1'], model:Optional[RetrievalModel]=None, alpha:str='0.6', tau:str='0.35', scores:list[RetrievalScore]=[]}` | `src/paperproof/schemas/docs.py:283` |
| `DocsPackV2` | `BaseModel(STRICT){schema_version:Literal['docs_pack.v2']='docs_pack.v2', pack_id:str, task_id:str, project_id:str, evidence_units:list[dict], documents_meta:list[dict], retrieval:RetrievalBlock}` | `src/paperproof/schemas/docs.py:298` |
| `FreezeItem` | `BaseModel(STRICT){schema_version:Literal['freeze_item.v1']='freeze_item.v1', freeze_id:str, project_id:str, action:Literal['freeze','unfreeze'], freeze_type:Literal['local_freeze','subtree_freeze','spine_freeze'], target_ids:list[str], evidence_ids:list[str], allowed_language:list[str], forbidden_language:list[str], revokes:Optional[str], created_at:str}` | `src/paperproof/schemas/freeze.py:12` |
| `Origin` | `BaseModel(STRICT){kind:Literal['seed','expansion','bridge'], source:str}` | `src/paperproof/schemas/graph.py:20` |
| `LanguageLimits` | `BaseModel(STRICT){allowed:list[str], forbidden:list[str]}` | `src/paperproof/schemas/graph.py:27` |
| `LogicNode` | `BaseModel(STRICT){schema_version:Literal['logic_node.v1']='logic_node.v1', node_id:str, project_id:str, bfs_id:str, layer:int, claim:str, claim_version:int, node_type:NodeType, scope:Scope, parents:list[str], origin:Origin, lifecycle_state:LifecycleState, state_reason:Optional[str], state_detail:Optional[dict[str,Any]], strength:Strength, language_limits:Optional[LanguageLimits], assumptions:list[str], evidence_bindings:list[str], latest_proof_result_id:Optional[str], frozen:bool, created_at:str}` | `src/paperproof/schemas/graph.py:34` |
| `LogicEdge` | `BaseModel(STRICT){schema_version:Literal['logic_edge.v1']='logic_edge.v1', edge_id:str, project_id:str, source_node_id:str, target_node_id:str, edge_type:EdgeType, edge_claim:str, claim_version:int, lifecycle_state:LifecycleState, state_reason:Optional[str], state_detail:Optional[dict[str,Any]], strength:Strength, language_limits:Optional[LanguageLimits], assumptions:list[str], frozen:bool, latest_proof_result_id:Optional[str], created_at:str}` | `src/paperproof/schemas/graph.py:60` |
| `Tombstone` | `BaseModel(STRICT){schema_version:Literal['tombstone.v1']='tombstone.v1', tombstone_id:str, project_id:str, target_type:Literal['node','edge'], target_id:str, reason:Literal['contradicted','out_of_scope','duplicate','endpoint_rejected'], duplicate_of:Optional[str], commit_id:str, created_at:str}` | `src/paperproof/schemas/graph.py:82` |
| `SnapshotFile` | `BaseModel(STRICT){sha256:str, rows:int}` | `src/paperproof/schemas/graph.py:96` |
| `Snapshot` | `BaseModel(STRICT){schema_version:Literal['snapshot.v1']='snapshot.v1', snapshot_id:str, files:dict[str,SnapshotFile], created_at:str}` | `src/paperproof/schemas/graph.py:103` |
| `ProposalNode` | `BaseModel(STRICT){claim:str, node_type:NodeType, scope:Scope, parents:list[str]=[]}` | `src/paperproof/schemas/graph.py:115` |
| `ProposalEdge` | `BaseModel(STRICT){source_ref:str, target_ref:str, edge_type:EdgeType, edge_claim:str}` | `src/paperproof/schemas/graph.py:124` |
| `ExpansionProposal` | `BaseModel(STRICT){schema_version:Literal['expansion_proposal.v1']='expansion_proposal.v1', proposal_id:str, project_id:str, bfs_id:str, layer:int, based_on_snapshot:str, nodes:list[ProposalNode], edges:list[ProposalEdge]}` | `src/paperproof/schemas/graph.py:133` |
| `Bundle` | `BaseModel(STRICT){task_file:str, context_pack:str, docs_pack:str}` | `src/paperproof/schemas/proof.py:25` |
| `ProofTask` | `BaseModel(STRICT){schema_version:Literal['proof_task.v1']='proof_task.v1', task_id:str, project_id:str, task_type:TaskType, target:dict[str,Any], context_pack:str, docs_pack:str, output_file:str}` | `src/paperproof/schemas/proof.py:33` |
| `ClaimDigestEntry` | `BaseModel(STRICT){node_id:str, claim:str}` | `src/paperproof/schemas/proof.py:46` |
| `ContextPack` | `BaseModel(STRICT){schema_version:Literal['context_pack.v1']='context_pack.v1', pack_id:str, task_id:str, project_id:str, based_on_snapshot:str, target:dict[str,Any], neighbor_nodes:list[dict], neighbor_edges:list[dict], claim_digest:list[ClaimDigestEntry], contract_scope:Scope, forbidden_claims:list[str], prior_results:list[dict], coverage:Optional[dict[str,Any]]=None}` | `src/paperproof/schemas/proof.py:53` |
| `DuplicateCheck` | `BaseModel(STRICT){duplicate:bool, duplicate_of:Optional[str]=None}` | `src/paperproof/schemas/proof.py:75` |
| `CheckForm` | `BaseModel(STRICT){scope_check:ScopeCheck, duplicate_check:DuplicateCheck, wellformed_check:WellformedCheck, evidence_check:EvidenceCheck, inference_check:Optional[InferenceCheck]=None} + @model_serializer` | `src/paperproof/schemas/proof.py:82` |
| `RepairProposal` | `BaseModel(STRICT){kind:Literal['bridge','narrow'], claim:Optional[str]=None, node_type:Optional[str]=None, narrowed_claim:Optional[str]=None} + @model_serializer` | `src/paperproof/schemas/proof.py:107` |
| `DocsRequestStub` | `BaseModel(STRICT){need:str, search_hints:list[str]}` | `src/paperproof/schemas/proof.py:125` |
| `ProofResult` | `BaseModel(STRICT){schema_version:Literal['proof_result.v1']='proof_result.v1', task_id:str, project_id:str, target_type:Literal['node','edge'], target_id:str, form:CheckForm, assumptions:list[str], evidence_used:list[str], language_limits:Optional[LanguageLimits], repair_proposals:list[RepairProposal], docs_requests:list[DocsRequestStub], notes:str}` | `src/paperproof/schemas/proof.py:132` |
| `ComputedVerdict` | `BaseModel(STRICT){verdict:Literal['pass','needs_repair','needs_docs','rejected'], repair_kind:Optional[Literal['bridge','narrow']]=None, strength:Optional[Literal['strong','conditional']]=None, reason:Optional[Literal['contradicted','out_of_scope','duplicate']]=None}` | `src/paperproof/schemas/proof.py:151` |
| `VerdictRecord` | `BaseModel(STRICT){schema_version:Literal['verdict_record.v1']='verdict_record.v1', proof_result_id:str, project_id:str, work_item_id:str, task_id:str, target_type:Literal['node','edge'], target_id:str, form:CheckForm, assumptions:list[str], evidence_used:list[str], language_limits:Optional[LanguageLimits], repair_proposals:list[RepairProposal], docs_requests:list[DocsRequestStub], notes:str, computed_verdict:ComputedVerdict, bundle:Bundle, validated_at:str}` | `src/paperproof/schemas/proof.py:160` |
| `Lease` | `BaseModel(STRICT){claimed_by:Optional[str]=None, claimed_at:Optional[str]=None, expires_at:Optional[str]=None, manifest:Optional[dict[str,Any]]=None}` | `src/paperproof/schemas/queue.py:25` |
| `WorkItem` | `BaseModel(STRICT){schema_version:Literal['work_item.v1']='work_item.v1', work_item_id:str, project_id:str, queue_name:QueueName, status:WorkStatus, target_type:Literal['node','edge','request','gap','section','wave'], target_id:str, task_id:Optional[str], bundle:Optional[dict[str,Any]], output_files:list[str], blocked_by:list[str], lease:Lease, attempt:int, created_at:str, updated_at:str}` | `src/paperproof/schemas/queue.py:34` |
| `QueueEvent` | `BaseModel(STRICT){schema_version:Literal['queue_event.v1']='queue_event.v1', event_id:str, project_id:str, work_item_id:str, op:QueueOp, from_status:Optional[WorkStatus], to_status:WorkStatus, actor:str, detail:dict[str,Any], created_at:str}` | `src/paperproof/schemas/queue.py:54` |
| `SearchFacets` | `BaseModel(STRICT){core_terms:list[str], scope_terms:list[str], counter_terms:list[str]}` | `src/paperproof/schemas/search.py:28` |
| `SearchQuery` | `BaseModel(STRICT){qid:str, kind:QueryKind, text:str}` | `src/paperproof/schemas/search.py:36` |
| `SearchStop` | `BaseModel(STRICT){max_queries:int, min_docs:int, min_eus:int}` | `src/paperproof/schemas/search.py:44` |
| `SearchPlan` | `BaseModel(STRICT){schema_version:Literal['search_plan.v1']='search_plan.v1', plan_id:str, request_id:str, project_id:str, angle:Angle, facets:SearchFacets, queries:list[SearchQuery], stop:SearchStop}` | `src/paperproof/schemas/search.py:52` |
| `WaveMember` | `BaseModel(STRICT){angle:Angle, work_item_id:str, plan_id:str, round:int=1, origin:Optional[str]=None}` | `src/paperproof/schemas/search.py:70` |
| `SearchWave` | `BaseModel(STRICT){schema_version:Literal['search_wave.v1']='search_wave.v1', wave_id:str, request_id:str, project_id:str, round:int, members:list[WaveMember], status:WaveStatus, created_at:str}` | `src/paperproof/schemas/search.py:87` |
| `AngleCoverage` | `BaseModel(STRICT){official_stats:Optional[AngleCovered]=None, academic:Optional[AngleCovered]=None, industry:Optional[AngleCovered]=None, counter:Optional[AngleCovered]=None, news:Optional[AngleCovered]=None}` | `src/paperproof/schemas/search.py:106` |
| `CoverageForm` | `BaseModel(STRICT){angle_covered:AngleCoverage, primary_source_present:Presence, disconfirming_captured:Presence}` | `src/paperproof/schemas/search.py:119` |
| `ExpectedSource` | `BaseModel(STRICT){name:str, why:str, suggested_query:str}` | `src/paperproof/schemas/search.py:127` |
| `CoverageReport` | `BaseModel(STRICT){schema_version:Literal['coverage_report.v1']='coverage_report.v1', wave_id:str, form:CoverageForm, expected_sources:list[ExpectedSource], notes:str}` | `src/paperproof/schemas/search.py:135` |
| `BfsPlanEntry` | `BaseModel(STRICT){bfs_id:str, purpose:str, depends_on:list[str]=[]}` | `src/paperproof/schemas/spec.py:21` |
| `PaperSpec` | `BaseModel(STRICT){schema_version:Literal['paper_spec.v1']='paper_spec.v1', project_id:str, paper_type:PaperType, core_question:str, intended_thesis:str, scope:Scope, hard_exclusions:list[str], seed_claims:list[str], known_sources:list[str], success_criteria:list[str], bfs_plan:list[BfsPlanEntry], source_files:list[str]=[]}` | `src/paperproof/schemas/spec.py:29` |
| `ProjectContract` | `BaseModel(STRICT){schema_version:Literal['project_contract.v1']='project_contract.v1', project_id:str, contract_version:int, fixed_question:str, outcome_direction:str, scope:Scope, in_scope:list[str], out_of_scope:list[str], forbidden_claims:list[str], success_criteria:list[str], accepted_by_user:bool, accepted_at:Optional[str]}` | `src/paperproof/schemas/spec.py:46` |
| **— Store (JSONL/locks) & Scoping —** | | |
| `merge_patch` | `def merge_patch(target: Any, patch: Any) -> Any` | `src/paperproof/scoping/build.py:40` |
| `build` | `def build(paths: Paths, topic_file: str \| Path, patch_file: str \| Path \| None = None) -> dict[str, Any]` | `src/paperproof/scoping/build.py:124` |
| `accept` | `def accept(paths: Paths) -> dict[str, Any]` | `src/paperproof/scoping/build.py:178` |
| `show` | `def show(paths: Paths) -> dict[str, Any]` | `src/paperproof/scoping/build.py:191` |
| `ParsedTopic` | `@dataclass ParsedTopic{sections: dict[str,str]={}, duplicates: list[str]=[], empty: list[str]=[], warnings: list[str]=[]; @property missing -> list[str]}` | `src/paperproof/scoping/parser.py:42` |
| `parse_topic` | `def parse_topic(text: str) -> ParsedTopic` | `src/paperproof/scoping/parser.py:79` |
| `parse_list` | `def parse_list(body: str) -> tuple[list[str], list[str]]` | `src/paperproof/scoping/parser.py:100` |
| `parse_scope` | `def parse_scope(scope_items: list[str]) -> dict[str, object]` | `src/paperproof/scoping/parser.py:119` |
| `PathSafetyError` | `class PathSafetyError(UsageError): exit_code = 2` | `src/paperproof/store/jsonl.py:21` |
| `safe_resolve` | `def safe_resolve(project_dir: str \| Path, relpath: str \| Path) -> Path` | `src/paperproof/store/jsonl.py:27` |
| `file_lock` | `@contextmanager def file_lock(path: str \| Path, mode: str = "a") -> Iterator[Any]` | `src/paperproof/store/jsonl.py:48` |
| `append` | `def append(path: str \| Path, record: Any) -> None` | `src/paperproof/store/jsonl.py:69` |
| `read_all` | `def read_all(path: str \| Path) -> list[dict[str, Any]]` | `src/paperproof/store/jsonl.py:76` |
| `latest_by_id` | `def latest_by_id(path: str \| Path, id_field: str) -> dict[str, dict[str, Any]]` | `src/paperproof/store/jsonl.py:97` |
| `latest_records` | `def latest_records(path: str \| Path, id_field: str) -> list[dict[str, Any]]` | `src/paperproof/store/jsonl.py:107` |
| `write_json` | `def write_json(path: str \| Path, record: Any) -> None` | `src/paperproof/store/jsonl.py:121` |
| `read_json` | `def read_json(path: str \| Path) -> dict[str, Any]` | `src/paperproof/store/jsonl.py:130` |
| `compute_files` | `def compute_files(paths: Paths) -> dict[str, SnapshotFile]` | `src/paperproof/store/snapshot.py:33` |
| `take_snapshot` | `def take_snapshot(paths: Paths, snapshot_id: str \| None = None) -> Snapshot` | `src/paperproof/store/snapshot.py:41` |
| `latest_snapshot_id` | `def latest_snapshot_id(paths: Paths) -> str \| None` | `src/paperproof/store/snapshot.py:55` |
| `verify_snapshot` | `def verify_snapshot(paths: Paths, snapshot_id: str) -> bool` | `src/paperproof/store/snapshot.py:60` |
| `is_current` | `def is_current(paths: Paths, snapshot_id: str) -> bool` | `src/paperproof/store/snapshot.py:78` |
| **— Graph, Expander & ProofTask builder —** | | |
| `validate` | `validate(paths: Paths, proposal_file: str \| Path) -> dict[str, Any]` | `src/paperproof/expander/ingest.py:36` |
| `ingest` | `ingest(paths: Paths, proposal_file: str \| Path, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/expander/ingest.py:61` |
| `list_nodes` | `list_nodes(paths: Paths, state: str \| None = None, lane: str \| None = None, layer: int \| None = None) -> dict[str, Any]` | `src/paperproof/graph/commands.py:23` |
| `list_edges` | `list_edges(paths: Paths, state: str \| None = None, lane: str \| None = None, layer: int \| None = None) -> dict[str, Any]` | `src/paperproof/graph/commands.py:37` |
| `show` | `show(paths: Paths, target_id: str) -> dict[str, Any]` | `src/paperproof/graph/commands.py:52` |
| `park` | `park(paths: Paths, target_id: str, reason: str, into: str \| None = None) -> dict[str, Any]` | `src/paperproof/graph/commands.py:66` |
| `unpark` | `unpark(paths: Paths, target_id: str) -> dict[str, Any]` | `src/paperproof/graph/commands.py:70` |
| `msa_check` | `msa_check(paths: Paths) -> dict[str, Any]` | `src/paperproof/graph/commands.py:94` |
| `GraphView` | `class GraphView(__init__(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None); indexes node_by_id/edge_by_id` | `src/paperproof/graph/model.py:21` |
| `load` | `load(paths: Paths) -> GraphView` | `src/paperproof/graph/model.py:173` |
| `load_tombstones` | `load_tombstones(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/graph/model.py:188` |
| `structural_signature` | `structural_signature(record: dict[str, Any]) -> tuple[Any, ...]` | `src/paperproof/graph/model.py:195` |
| `trace_node` | `trace_node(paths: Paths, node_id: str) -> dict[str, Any]` | `src/paperproof/graph/trace.py:59` |
| `build_bundle` | `build_bundle(paths: Paths, work_item: dict[str, Any]) -> dict[str, Any]` | `src/paperproof/prooftask/builder.py:56` |
| `build_frontier` | `build_frontier(paths: Paths, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/prooftask/builder.py:178` |
| `build_one` | `build_one(paths: Paths, target_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/prooftask/builder.py:215` |
| **— Validate core + rules A (spec/exp/node-edge/task/commit) —** | | |
| `Failure` | `@dataclass(frozen=True) Failure{rule_id: str, detail: str = ""}` | `src/paperproof/validate/envelope.py:14` |
| `to_envelope` | `to_envelope(failures: list[Failure]) -> dict[str, Any]` | `src/paperproof/validate/envelope.py:19` |
| `validate_result` | `validate_result(paths: Paths, output_file: str, work_item_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/validate/proof.py:40` |
| `Rule` | `@dataclass(frozen=True) Rule{rule_id: str, prefix: str, description: str}` | `src/paperproof/validate/registry.py:22` |
| `rule_ids` | `rule_ids() -> list[str]` | `src/paperproof/validate/registry.py:146` |
| `verify_commits` | `verify_commits(paths: Paths) -> list[Failure]` | `src/paperproof/validate/rules/v_commit.py:25` |
| `lane_complete` | `lane_complete(paths: Paths, gv: graph_model.GraphView, bfs_id: str) -> bool` | `src/paperproof/validate/rules/v_exp.py:58` |
| `check` | `check(paths: Paths, proposal: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_exp.py:75` |
| `node02_ok` | `node02_ok(claim: str) -> tuple[bool, str]` | `src/paperproof/validate/rules/v_node_edge.py:20` |
| `node03_ok` | `node03_ok(node_scope: dict[str, Any], contract_scope: dict[str, Any]) -> tuple[bool, str]` | `src/paperproof/validate/rules/v_node_edge.py:31` |
| `edge02_ok` | `edge02_ok(edge_claim: str, source_claim: str, target_claim: str) -> tuple[bool, str]` | `src/paperproof/validate/rules/v_node_edge.py:40` |
| `no_supports_cycle` | `no_supports_cycle(edges: list[dict[str, Any]]) -> tuple[bool, str]` | `src/paperproof/validate/rules/v_node_edge.py:48` |
| `graph_record_checks` | `graph_record_checks(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[Failure]` | `src/paperproof/validate/rules/v_node_edge.py:77` |
| `check` | `check(parsed: Any, spec_dict: dict[str, Any], contract_dict: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_spec.py:58` |
| `check_context_pack` | `check_context_pack(paths: Paths, context_pack: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_task.py:19` |
| `check_docs_pack` | `check_docs_pack(paths: Paths, docs_pack: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_task.py:43` |
| **— Validate rules B (pr/path/q/dr/sp/src/sem/wave/cov/sweep) —** | | |
| `check_context_pack_coverage` | `def check_context_pack_coverage(ctx_pack: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_cov.py:37` |
| `check_born_dead_reason` | `def check_born_dead_reason(reason: str, floor_met: bool \| None = None) -> list[Failure]` | `src/paperproof/validate/rules/v_cov.py:63` |
| `core_terms` | `def core_terms(text: str) -> set[str]` | `src/paperproof/validate/rules/v_cov.py:78` |
| `rounds_reset_on_narrow` | `def rounds_reset_on_narrow(parent_claim: str, narrowed_claim: str) -> bool` | `src/paperproof/validate/rules/v_cov.py:83` |
| `raw_scan` | `def raw_scan(raw: Any) -> list[Failure]` | `src/paperproof/validate/rules/v_dr.py:37` |
| `check` | `def check(result_dict: dict[str, Any], *, archived_doc_ids: set[str] \| None = None, archived_texts: dict[str, str] \| None = None) -> list[Failure]` | `src/paperproof/validate/rules/v_dr.py:61` |
| `check_output_path` | `def check_output_path(actual_relpath: str, declared_output_files: list[str]) -> list[Failure]` | `src/paperproof/validate/rules/v_path.py:28` |
| `check_path_safety` | `def check_path_safety(project_dir: str \| Path, relpath: str) -> list[Failure]` | `src/paperproof/validate/rules/v_path.py:40` |
| `check_utf8_json` | `def check_utf8_json(project_dir: str \| Path, relpath: str, kind: str = "json") -> list[Failure]` | `src/paperproof/validate/rules/v_path.py:49` |
| `build_manifest` | `def build_manifest(project_dir: str \| Path, relpaths: list[str]) -> dict[str, dict[str, Any]]` | `src/paperproof/validate/rules/v_path.py:70` |
| `check_prefix_rule` | `def check_prefix_rule(project_dir: str \| Path, manifest: dict[str, dict[str, Any]]) -> list[Failure]` | `src/paperproof/validate/rules/v_path.py:81` |
| `check_lease_scan` | `def check_lease_scan(project_dir: str \| Path, lease_manifest: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_path.py:123` |
| `build_lease_manifest` | `def build_lease_manifest(project_dir: str \| Path, allowed_write_paths: list[str]) -> dict[str, Any]` | `src/paperproof/validate/rules/v_path.py:138` |
| `raw_scan` | `def raw_scan(raw: Any) -> list[Failure]` | `src/paperproof/validate/rules/v_pr.py:35` |
| `check` | `def check(result_dict: dict[str, Any], *, task: dict[str, Any], context_pack: dict[str, Any], docs_pack: dict[str, Any], work_item: dict[str, Any]) -> tuple[list[Failure], dict[str, Any] \| None]` | `src/paperproof/validate/rules/v_pr.py:64` |
| `transition_legal` | `def transition_legal(from_status: Any, op: str, to_status: str) -> bool` | `src/paperproof/validate/rules/v_q.py:24` |
| `verify_queue` | `def verify_queue(paths: Paths) -> list[Failure]` | `src/paperproof/validate/rules/v_q.py:29` |
| `check_pack` | `def check_pack(pack: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_sem.py:28` |
| `check_no_similarity_fulfillment` | `def check_no_similarity_fulfillment(requests: list[dict[str, Any]]) -> list[Failure]` | `src/paperproof/validate/rules/v_sem.py:64` |
| `check` | `def check(result_dict: dict[str, Any], plan: dict[str, Any] \| None) -> list[Failure]` | `src/paperproof/validate/rules/v_sp.py:23` |
| `check_document_provenance` | `def check_document_provenance(doc: dict[str, Any]) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:38` |
| `check_secondary_quote` | `def check_secondary_quote(doc: dict[str, Any], archived_doc_ids: set[str]) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:57` |
| `check_registry_history` | `def check_registry_history(profile_records: list[dict[str, Any]]) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:75` |
| `check_triangulation` | `def check_triangulation(binding_docmeta: list[tuple[str, str, str]]) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:102` |
| `check_registry_excerpt` | `def check_registry_excerpt(all_profiles: list[dict[str, Any]], facet_text: str, excerpt_source_ids: set[str]) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:118` |
| `verify_sources` | `def verify_sources(paths: Paths) -> list[Failure]` | `src/paperproof/validate/rules/v_src.py:140` |
| `seed_fact_mechanism_nodes` | `def seed_fact_mechanism_nodes(gv: graph_model.GraphView) -> list[dict[str, Any]]` | `src/paperproof/validate/rules/v_sweep.py:29` |
| `node_meets_floor` | `def node_meets_floor(paths: Paths, node: dict[str, Any], eus: list[dict[str, Any]] \| None = None, requests: list[dict[str, Any]] \| None = None) -> bool` | `src/paperproof/validate/rules/v_sweep.py:40` |
| `coverage` | `def coverage(paths: Paths, gv: graph_model.GraphView) -> dict[str, Any]` | `src/paperproof/validate/rules/v_sweep.py:66` |
| `check_sweep_floor` | `def check_sweep_floor(paths: Paths, gv: graph_model.GraphView) -> list[Failure]` | `src/paperproof/validate/rules/v_sweep.py:82` |
| `check_member_paths` | `def check_member_paths(output_paths: list[str]) -> list[Failure]` | `src/paperproof/validate/rules/v_wave.py:32` |
| `check_merge` | `def check_merge(member_results: list[dict[str, Any]], merged: dict[str, Any], request_id: str, project_id: str) -> list[Failure]` | `src/paperproof/validate/rules/v_wave.py:58` |
| `check_critic` | `def check_critic(raw: dict[str, Any], mandatory: tuple[str, ...]) -> list[Failure]` | `src/paperproof/validate/rules/v_wave.py:101` |
| `check_wave_rounds` | `def check_wave_rounds(wave: dict[str, Any], r_max: int = R_MAX) -> list[Failure]` | `src/paperproof/validate/rules/v_wave.py:137` |
| `check_single_dres` | `def check_single_dres(request_id: str, request_records: list[dict[str, Any]]) -> list[Failure]` | `src/paperproof/validate/rules/v_wave.py:154` |
| **— Committer (sole graph mutator) —** | | |
| `apply_proof_verdict` | `apply_proof_verdict(paths: Paths, pr_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:162` |
| `apply_expansion` | `apply_expansion(paths: Paths, proposal: dict[str, Any], actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:575` |
| `park` | `park(paths: Paths, target_id: str, reason: str, into: str \| None = None, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:693` |
| `unpark` | `unpark(paths: Paths, target_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:724` |
| `freeze_batch` | `freeze_batch(paths: Paths, target_ids: list[str], input_ref: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:749` |
| `unfreeze_batch` | `unfreeze_batch(paths: Paths, target_ids: list[str], input_ref: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:766` |
| `contract_reopen` | `contract_reopen(paths: Paths, target_ids: list[str], input_ref: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/committer/apply.py:788` |
| `compute_verdict` | `compute_verdict(form: dict[str, Any], task_type: str, assumptions: list[str] \| None = None) -> dict[str, Any]` | `src/paperproof/committer/decision_table.py:43` |
| `ladder_check` | `ladder_check(form: dict[str, Any], task_type: str, assumptions: list[str] \| None = None, node_type: str \| None = None) -> list[str]` | `src/paperproof/committer/decision_table.py:85` |
| `replay_reproduces` | `replay_reproduces(paths: Paths, commit_id: str) -> bool` | `src/paperproof/committer/replay.py:56` |
| **— Docs database A (ingest/cache/matcher/pack) —** | | |
| `fingerprint_hit` | `def fingerprint_hit(paths: Paths, fp: str) -> bool` | `src/paperproof/docsdb/cache.py:29` |
| `is_cache_hit` | `def is_cache_hit(paths: Paths, fp: str, target_record: dict[str, Any]) -> bool` | `src/paperproof/docsdb/cache.py:45` |
| `ingest_file` | `def ingest_file(paths: Paths, file_path: str, source_type: str \| None = None, title: str \| None = None, citation_key: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/ingest.py:57` |
| `ingest_result` | `def ingest_result(paths: Paths, output_file: str, work_item_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/ingest.py:182` |
| `ingest_merged` | `def ingest_merged(paths: Paths, request_id: str, merged_relpath: str, actor: str, extracted_by: str = "docs-merger") -> dict[str, Any]` | `src/paperproof/docsdb/ingest.py:320` |
| `score` | `def score(claim: str, eu: dict[str, Any]) -> int` | `src/paperproof/docsdb/matcher.py:39` |
| `match` | `def match(claim: str, target_scope: dict[str, Any] \| None, evidence_units: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]` | `src/paperproof/docsdb/matcher.py:44` |
| `hybrid_score` | `def hybrid_score(claim: str, target_scope: dict[str, Any] \| None, evidence_units: list[dict[str, Any]], eu_vectors: dict[str, Vector] \| None, claim_vector: Optional[Vector]) -> tuple[list[tuple[float, dict[str, Any]]], dict[str, dict[str, float]]]` | `src/paperproof/docsdb/matcher.py:99` |
| `cluster_near_dups` | `def cluster_near_dups(eus: list[dict[str, Any]], eu_vectors: dict[str, Vector] \| None, tau: float = CLUSTER_TAU) -> tuple[list[dict[str, Any]], dict[str, list[str]]]` | `src/paperproof/docsdb/matcher.py:139` |
| `fingerprint` | `def fingerprint(need: str, search_hints: list[str] \| None) -> str` | `src/paperproof/docsdb/matcher.py:205` |
| `assemble` | `def assemble(paths: Paths, target_record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` | `src/paperproof/docsdb/pack.py:95` |
| `assemble_v2` | `def assemble_v2(paths: Paths, target_record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[str]]` | `src/paperproof/docsdb/pack.py:114` |
| `search` | `def search(paths: Paths, query: str, scope: dict[str, Any] \| None = None, semantic_flag: bool = False) -> dict[str, Any]` | `src/paperproof/docsdb/pack.py:185` |
| **— Docs database B (planner/registry/wave/coverage/commands) —** | | |
| `ingest_file` | `ingest_file(paths: Paths, file_path: str, source_type: str \| None, title: str \| None, citation_key: str \| None) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:27` |
| `search` | `search(paths: Paths, query: str, scope: str \| None = None, semantic: bool = False) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:31` |
| `build_pack` | `build_pack(paths: Paths, task_id: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:48` |
| `semantic_rebuild` | `semantic_rebuild(paths: Paths) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:80` |
| `semantic_check` | `semantic_check(paths: Paths) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:87` |
| `request` | `request(paths: Paths, target_id: str, need: str, hints: list[str] \| None, actor: str \| None = None, fan: bool = False) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:94` |
| `plan` | `plan(paths: Paths, request_id: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:128` |
| `wave` | `wave(paths: Paths, request_id: str, fan: bool = False, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:138` |
| `ingest_result` | `ingest_result(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:151` |
| `wave_member` | `wave_member(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:155` |
| `wave_resolve` | `wave_resolve(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:162` |
| `coverage` | `coverage(paths: Paths, node: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:168` |
| `source_list` | `source_list(paths: Paths) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:179` |
| `source_set` | `source_set(paths: Paths, domain: str, tier: str \| None = None, publisher: str \| None = None, workaround: str \| None = None, note: str \| None = None, blocked: bool \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:185` |
| `validate_docs_result` | `validate_docs_result(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]` | `src/paperproof/docsdb/commands.py:240` |
| `CoverageContext` | `@dataclass CoverageContext{spine_ids: set[str]; eus_by_id, docs_by_id, sources_by_domain: dict; requests_latest: list; wave_by_request: dict; coverage_reports_by_wave: dict; single_query_logs: dict; docs_by_dres: dict=field({}); terminal_member_ids: set=field(set); plan_counter_qid: dict=field({}); rounds_reset_at: dict=field({})}` | `src/paperproof/docsdb/coverage.py:80` |
| `build_context` | `build_context(paths: Paths, spine_ids: set[str]) -> CoverageContext` | `src/paperproof/docsdb/coverage.py:102` |
| `triangulated` | `triangulated(binding_docmeta: list[tuple[str, str, str]]) -> bool` | `src/paperproof/docsdb/coverage.py:245` |
| `classify_role` | `classify_role(node: dict[str, Any], spine_ids: set[str]) -> str` | `src/paperproof/docsdb/coverage.py:273` |
| `binding_docmeta` | `binding_docmeta(node: dict[str, Any], ctx: CoverageContext) -> list[tuple[str, str, str]]` | `src/paperproof/docsdb/coverage.py:312` |
| `is_saturated` | `is_saturated(rounds: int, angles: dict[str, str], new_docs_last_round: int, mandatory: tuple[str, ...]) -> bool` | `src/paperproof/docsdb/coverage.py:468` |
| `target_ledger` | `target_ledger(target_record: dict[str, Any], ctx: CoverageContext) -> dict[str, Any]` | `src/paperproof/docsdb/coverage.py:479` |
| `meets_floor` | `meets_floor(ledger: dict[str, Any]) -> bool` | `src/paperproof/docsdb/coverage.py:540` |
| `floor_line` | `floor_line(ledger: dict[str, Any]) -> str` | `src/paperproof/docsdb/coverage.py:544` |
| `build_ledger` | `build_ledger(paths: Paths) -> dict[str, Any]` | `src/paperproof/docsdb/coverage.py:570` |
| `ledger_for` | `ledger_for(paths: Paths, node_id: str) -> dict[str, Any]` | `src/paperproof/docsdb/coverage.py:585` |
| `compile_plan` | `compile_plan(request_id: str, project_id: str, angle: str, need: str, search_hints: list[str], target_scope: dict[str, Any] \| None, contract_scope: dict[str, Any] \| None) -> SearchPlan` | `src/paperproof/docsdb/planner.py:101` |
| `plan_relpath` | `plan_relpath(request_id: str) -> str` | `src/paperproof/docsdb/planner.py:181` |
| `plan_path` | `plan_path(paths: Paths, request_id: str) -> Path` | `src/paperproof/docsdb/planner.py:185` |
| `load_plan` | `load_plan(paths: Paths, request_id: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/planner.py:189` |
| `plan_for_request` | `plan_for_request(paths: Paths, request_id: str, angle: str = DEFAULT_ANGLE) -> dict[str, Any]` | `src/paperproof/docsdb/planner.py:203` |
| `wave_plan_relpath` | `wave_plan_relpath(request_id: str, angle: str) -> str` | `src/paperproof/docsdb/planner.py:227` |
| `plan_id_relpath` | `plan_id_relpath(plan_id: str) -> str` | `src/paperproof/docsdb/planner.py:231` |
| `load_plan_by_id` | `load_plan_by_id(paths: Paths, plan_id: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/planner.py:237` |
| `load_wave_plan` | `load_wave_plan(paths: Paths, request_id: str, angle: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/planner.py:247` |
| `plan_for_wave_member` | `plan_for_wave_member(paths: Paths, request_id: str, angle: str, extra_hints: list[str] \| None = None, plan_id: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/planner.py:254` |
| `tier_for` | `tier_for(source_type: str) -> str` | `src/paperproof/docsdb/registry.py:57` |
| `domain_from_url` | `domain_from_url(url: Optional[str]) -> Optional[str]` | `src/paperproof/docsdb/registry.py:62` |
| `load_all` | `load_all(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/docsdb/registry.py:77` |
| `load_latest` | `load_latest(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/docsdb/registry.py:82` |
| `learn` | `learn(paths: Paths, doc_domains: list[tuple[str, str]], result: dict[str, Any] \| None, now: str \| None = None) -> dict[str, str]` | `src/paperproof/docsdb/registry.py:124` |
| `profile_matches_facets` | `profile_matches_facets(profile: dict[str, Any], facet_text: str) -> bool` | `src/paperproof/docsdb/registry.py:199` |
| `matched_profiles` | `matched_profiles(paths: Paths, need: str, hints: list[str] \| None = None, scope: dict[str, Any] \| None = None) -> list[dict[str, Any]]` | `src/paperproof/docsdb/registry.py:218` |
| `render_excerpt` | `render_excerpt(profiles: list[dict[str, Any]]) -> str` | `src/paperproof/docsdb/registry.py:228` |
| `canonical_url` | `canonical_url(url: str \| None) -> str \| None` | `src/paperproof/docsdb/wave.py:64` |
| `merge_results` | `merge_results(request_id: str, project_id: str, member_results: list[dict[str, Any]]) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:99` |
| `wave_verdict` | `wave_verdict(form: dict[str, Any], round: int, r_max: int = R_MAX, mandatory: tuple[str, ...] = MANDATORY_ANGLES) -> str` | `src/paperproof/docsdb/wave.py:207` |
| `followup_specs` | `followup_specs(form: dict[str, Any], expected_sources: list[dict[str, Any]], mandatory: tuple[str, ...] = MANDATORY_ANGLES) -> list[dict[str, Any]]` | `src/paperproof/docsdb/wave.py:229` |
| `load_waves` | `load_waves(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/docsdb/wave.py:258` |
| `wave_by_id` | `wave_by_id(paths: Paths, wave_id: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/wave.py:262` |
| `wave_for_request` | `wave_for_request(paths: Paths, request_id: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/wave.py:266` |
| `member_plan_id` | `member_plan_id(request_id: str, angle: str, round: int, origin: str \| None) -> str` | `src/paperproof/docsdb/wave.py:323` |
| `member_output` | `member_output(request_id: str, angle: str, round: int, origin: str \| None) -> str` | `src/paperproof/docsdb/wave.py:336` |
| `start_wave` | `start_wave(paths: Paths, request_id: str, fan: bool = False, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:364` |
| `wave_for_member` | `wave_for_member(paths: Paths, wi_id: str) -> dict[str, Any] \| None` | `src/paperproof/docsdb/wave.py:402` |
| `complete_member` | `complete_member(paths: Paths, wave_id: str, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:410` |
| `merged_relpath` | `merged_relpath(request_id: str) -> str` | `src/paperproof/docsdb/wave.py:505` |
| `merge` | `merge(paths: Paths, wave_id: str) -> str` | `src/paperproof/docsdb/wave.py:509` |
| `open_critic` | `open_critic(paths: Paths, wave_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:528` |
| `resolve_critic` | `resolve_critic(paths: Paths, wave_id: str, critic_wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:543` |
| `wave_member_ingest` | `wave_member_ingest(paths: Paths, output_file: str, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:627` |
| `wave_resolve` | `wave_resolve(paths: Paths, coverage_report_file: str, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/docsdb/wave.py:653` |
| **— Queue engine & Freeze gate —** | | |
| `compute_closure` | `compute_closure(gv: graph_model.GraphView, freeze_type: str, target: str) -> set[str]` | `src/paperproof/freeze/apply.py:76` |
| `touches` | `touches(gv: graph_model.GraphView, closure: set[str], target_id: str) -> bool` | `src/paperproof/freeze/apply.py:94` |
| `apply` | `apply(paths: Paths, target: str, level: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/freeze/apply.py:201` |
| `unfreeze` | `unfreeze(paths: Paths, target: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/freeze/apply.py:261` |
| `list_items` | `list_items(paths: Paths, queue: str \| None = None, status: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/commands.py:18` |
| `claim` | `claim(paths: Paths, queue: str, agent: str, wi_id: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/commands.py:53` |
| `heartbeat` | `heartbeat(paths: Paths, wi_id: str, agent: str) -> dict[str, Any]` | `src/paperproof/queue/commands.py:58` |
| `release` | `release(paths: Paths, wi_id: str) -> dict[str, Any]` | `src/paperproof/queue/commands.py:63` |
| `complete` | `complete(paths: Paths, wi_id: str) -> dict[str, Any]` | `src/paperproof/queue/commands.py:68` |
| `fail` | `fail(paths: Paths, wi_id: str, reason: str) -> dict[str, Any]` | `src/paperproof/queue/commands.py:73` |
| `expire` | `expire(paths: Paths) -> dict[str, Any]` | `src/paperproof/queue/commands.py:78` |
| `requeue` | `requeue(paths: Paths, wi_id: str) -> dict[str, Any]` | `src/paperproof/queue/commands.py:87` |
| `events` | `events(paths: Paths, after: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/commands.py:92` |
| `load_items` | `load_items(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/queue/engine.py:89` |
| `items_by_id` | `items_by_id(paths: Paths) -> dict[str, dict[str, Any]]` | `src/paperproof/queue/engine.py:93` |
| `load_events` | `load_events(paths: Paths) -> list[dict[str, Any]]` | `src/paperproof/queue/engine.py:97` |
| `get_item` | `get_item(paths: Paths, wi_id: str) -> dict[str, Any]` | `src/paperproof/queue/engine.py:101` |
| `enqueue` | `enqueue(paths, *, queue_name, target_type, target_id, task_id=None, bundle=None, output_files=None, blocked_by=None, actor) -> dict[str, Any]` | `src/paperproof/queue/engine.py:178` |
| `dead_letter_born` | `dead_letter_born(paths, *, queue_name, target_type, target_id, blocked_by=None, reason, actor, detail=None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:224` |
| `expire_sweep` | `expire_sweep(paths: Paths, actor: str \| None = None) -> list[str]` | `src/paperproof/queue/engine.py:276` |
| `is_claimable` | `is_claimable(paths: Paths, item: dict[str, Any], gv: graph_model.GraphView \| None = None) -> bool` | `src/paperproof/queue/engine.py:317` |
| `unblock_sweep` | `unblock_sweep(paths: Paths, actor: str \| None = None) -> list[str]` | `src/paperproof/queue/engine.py:328` |
| `run_sweeps` | `run_sweeps(paths: Paths, actor: str \| None = None) -> dict[str, list[str]]` | `src/paperproof/queue/engine.py:348` |
| `claim` | `claim(paths: Paths, *, queue_name: str, agent: str, wi_id: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:355` |
| `heartbeat` | `heartbeat(paths: Paths, wi_id: str, agent: str) -> dict[str, Any]` | `src/paperproof/queue/engine.py:396` |
| `release` | `release(paths: Paths, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:407` |
| `complete` | `complete(paths: Paths, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:417` |
| `fail` | `fail(paths: Paths, wi_id: str, reason: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:440` |
| `validate_pass` | `validate_pass(paths: Paths, wi_id: str, actor: str \| None = None, detail: dict[str, Any] \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:450` |
| `validate_fail` | `validate_fail(paths, wi_id, failed_rules, actor=None, detail=None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:457` |
| `requeue` | `requeue(paths: Paths, wi_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:480` |
| `attach_bundle` | `attach_bundle(paths, wi_id, task_id, bundle, output_files) -> dict[str, Any]` | `src/paperproof/queue/engine.py:493` |
| `commit_item` | `commit_item(paths: Paths, wi_id: str, actor: str) -> dict[str, Any]` | `src/paperproof/queue/engine.py:507` |
| `invalidate` | `invalidate(paths: Paths, wi_id: str, actor: str, detail: dict[str, Any] \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:512` |
| `cancel` | `cancel(paths: Paths, wi_id: str, actor: str, detail: dict[str, Any] \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:517` |
| `rebuild` | `rebuild(paths: Paths, wi_id: str, actor: str, to_blocked: bool = False, changes: dict[str, Any] \| None = None) -> dict[str, Any]` | `src/paperproof/queue/engine.py:522` |
| **— Compiler & Audit —** | | |
| `run` | `run(paths: Paths, draft_map_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/audit/run.py:67` |
| `draft_map` | `draft_map(paths: Paths, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/compiler/draft_map.py:51` |
| `load_draft_map` | `load_draft_map(paths: Paths, draft_map_id: str) -> dict[str, Any] \| None` | `src/paperproof/compiler/draft_map.py:120` |
| `latest_draft_map` | `latest_draft_map(paths: Paths) -> dict[str, Any] \| None` | `src/paperproof/compiler/draft_map.py:127` |
| `detect_gaps` | `detect_gaps(paths: Paths, gv: graph_model.GraphView, spine_ids: set[str], plan: list[dict[str, Any]]) -> list[dict[str, Any]]` | `src/paperproof/compiler/dry_run.py:44` |
| `spine_freeze_current` | `spine_freeze_current(paths: Paths, gv: graph_model.GraphView, spine_ids: set[str]) -> bool` | `src/paperproof/compiler/dry_run.py:103` |
| `dry_run` | `dry_run(paths: Paths, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/compiler/dry_run.py:163` |
| `check_prose` | `check_prose(text: str, section: dict[str, Any]) -> list[Failure]` | `src/paperproof/compiler/prose.py:48` |
| `ingest_prose` | `ingest_prose(paths: Paths, output_file: str, work_item_id: str, actor: str \| None = None) -> dict[str, Any]` | `src/paperproof/compiler/prose.py:117` |
| `assign` | `assign(gv: graph_model.GraphView, spine_ids: set[str]) -> dict[str, list[dict[str, Any]]]` | `src/paperproof/compiler/section_plan.py:52` |
| `build` | `build(gv: graph_model.GraphView, spine_ids: set[str]) -> list[dict[str, Any]]` | `src/paperproof/compiler/section_plan.py:65` |
| **— Prompts (renderers) & CLI —** | | |
| `EnvelopeGroup` | `class EnvelopeGroup(TyperGroup); method main(self, *args: Any, **kwargs: Any) -> Any` | `src/paperproof/cli/app.py:108` |
| `AppState` | `@dataclass AppState{root: str, project: Optional[str]}` | `src/paperproof/cli/app.py:161` |
| `project_init` | `def project_init(ctx: typer.Context, project_id: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:200` |
| `project_status` | `def project_status(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:206` |
| `spec_build` | `def spec_build(ctx: typer.Context, topic_file: str = typer.Argument(...), patch: Optional[str] = typer.Option(None, '--patch')) -> None` | `src/paperproof/cli/app.py:235` |
| `spec_accept` | `def spec_accept(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:245` |
| `spec_show` | `def spec_show(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:251` |
| `db_rebuild` | `def db_rebuild(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:269` |
| `db_check` | `def db_check(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:275` |
| `db_semantic_rebuild` | `def db_semantic_rebuild(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:285` |
| `db_semantic_check` | `def db_semantic_check(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:297` |
| `ui_serve` | `def ui_serve(ctx: typer.Context, port: int = typer.Option(8420, '--port'), auto_rebuild: bool = typer.Option(False, '--auto-rebuild')) -> None` | `src/paperproof/cli/app.py:322` |
| `graph_list_nodes` | `def graph_list_nodes(ctx: typer.Context, state: Optional[str] = typer.Option(None, '--state'), lane: Optional[str] = typer.Option(None, '--lane'), layer: Optional[int] = typer.Option(None, '--layer')) -> None` | `src/paperproof/cli/app.py:358` |
| `graph_list_edges` | `def graph_list_edges(ctx: typer.Context, state: Optional[str] = typer.Option(None, '--state'), lane: Optional[str] = typer.Option(None, '--lane'), layer: Optional[int] = typer.Option(None, '--layer')) -> None` | `src/paperproof/cli/app.py:369` |
| `graph_show` | `def graph_show(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:380` |
| `graph_msa_check` | `def graph_msa_check(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:386` |
| `graph_park` | `def graph_park(ctx: typer.Context, target_id: str = typer.Argument(...), reason: str = typer.Option(..., '--reason'), into: Optional[str] = typer.Option(None, '--into')) -> None` | `src/paperproof/cli/app.py:399` |
| `graph_unpark` | `def graph_unpark(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:410` |
| `expand_ingest` | `def expand_ingest(ctx: typer.Context, proposal_file: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:423` |
| `proof_build_tasks` | `def proof_build_tasks(ctx: typer.Context, frontier: bool = typer.Option(True, '--frontier', ...)) -> None` | `src/paperproof/cli/app.py:436` |
| `proof_build_task` | `def proof_build_task(ctx: typer.Context, target_id: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:449` |
| `proof_render_prompt` | `def proof_render_prompt(ctx: typer.Context, work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:455` |
| `queue_list` | `def queue_list(ctx: typer.Context, queue: Optional[str] = typer.Option(None, '--queue'), status: Optional[str] = typer.Option(None, '--status')) -> None` | `src/paperproof/cli/app.py:476` |
| `queue_claim` | `def queue_claim(ctx: typer.Context, queue: str = typer.Option(..., '--queue'), agent: str = typer.Option(..., '--agent'), id: Optional[str] = typer.Option(None, '--id')) -> None` | `src/paperproof/cli/app.py:486` |
| `queue_heartbeat` | `def queue_heartbeat(ctx: typer.Context, wi: str = typer.Argument(...), agent: str = typer.Option(..., '--agent')) -> None` | `src/paperproof/cli/app.py:497` |
| `queue_release` | `def queue_release(ctx: typer.Context, wi: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:503` |
| `queue_complete` | `def queue_complete(ctx: typer.Context, wi: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:509` |
| `queue_fail` | `def queue_fail(ctx: typer.Context, wi: str = typer.Argument(...), reason: str = typer.Option('manual fail', '--reason')) -> None` | `src/paperproof/cli/app.py:515` |
| `queue_expire` | `def queue_expire(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:521` |
| `queue_requeue` | `def queue_requeue(ctx: typer.Context, wi: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:527` |
| `queue_events` | `def queue_events(ctx: typer.Context, after: Optional[str] = typer.Option(None, '--after')) -> None` | `src/paperproof/cli/app.py:533` |
| `validate_result` | `def validate_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:546` |
| `validate_proposal` | `def validate_proposal(ctx: typer.Context, file: str = typer.Argument(...)) -> None` | `src/paperproof/cli/app.py:552` |
| `validate_docs_result` | `def validate_docs_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:565` |
| `docs_ingest` | `def docs_ingest(ctx: typer.Context, file: str = typer.Argument(...), source_type: Optional[str] = typer.Option(None, '--source-type'), title: Optional[str] = typer.Option(None, '--title'), citation_key: Optional[str] = typer.Option(None, '--citation-key')) -> None` | `src/paperproof/cli/app.py:578` |
| `docs_search` | `def docs_search(ctx: typer.Context, query: str = typer.Option(..., '--query'), scope: Optional[str] = typer.Option(None, '--scope'), semantic: bool = typer.Option(False, '--semantic')) -> None` | `src/paperproof/cli/app.py:590` |
| `docs_build_pack` | `def docs_build_pack(ctx: typer.Context, task: str = typer.Option(..., '--task')) -> None` | `src/paperproof/cli/app.py:601` |
| `docs_request` | `def docs_request(ctx: typer.Context, target: str = typer.Option(..., '--target'), need: str = typer.Option(..., '--need'), hint: list[str] = typer.Option(None, '--hint'), fan: bool = typer.Option(False, '--fan')) -> None` | `src/paperproof/cli/app.py:607` |
| `docs_ingest_result` | `def docs_ingest_result(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:619` |
| `docs_plan` | `def docs_plan(ctx: typer.Context, request: str = typer.Option(..., '--request')) -> None` | `src/paperproof/cli/app.py:625` |
| `docs_wave` | `def docs_wave(ctx: typer.Context, request: str = typer.Option(..., '--request'), fan: bool = typer.Option(False, '--fan')) -> None` | `src/paperproof/cli/app.py:631` |
| `docs_render_prompt` | `def docs_render_prompt(ctx: typer.Context, work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:641` |
| `docs_wave_member` | `def docs_wave_member(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:656` |
| `docs_wave_resolve` | `def docs_wave_resolve(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:668` |
| `docs_coverage` | `def docs_coverage(ctx: typer.Context, node: Optional[str] = typer.Option(None, '--node')) -> None` | `src/paperproof/cli/app.py:680` |
| `docs_source_list` | `def docs_source_list(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:695` |
| `docs_source_set` | `def docs_source_set(ctx: typer.Context, domain: str = typer.Option(..., '--domain'), tier: Optional[str] = typer.Option(None, '--tier'), publisher: Optional[str] = typer.Option(None, '--publisher'), workaround: Optional[str] = typer.Option(None, '--workaround'), note: Optional[str] = typer.Option(None, '--note'), blocked: Optional[bool] = typer.Option(None, '--blocked/--no-blocked')) -> None` | `src/paperproof/cli/app.py:701` |
| `commit_apply` | `def commit_apply(ctx: typer.Context, result: str = typer.Option(..., '--result')) -> None` | `src/paperproof/cli/app.py:728` |
| `freeze_apply` | `def freeze_apply(ctx: typer.Context, target: str = typer.Option(..., '--target'), level: str = typer.Option(..., '--level')) -> None` | `src/paperproof/cli/app.py:748` |
| `freeze_unfreeze` | `def freeze_unfreeze(ctx: typer.Context, target: str = typer.Option(..., '--target')) -> None` | `src/paperproof/cli/app.py:758` |
| `compiler_dry_run` | `def compiler_dry_run(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:771` |
| `compiler_draft_map` | `def compiler_draft_map(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:777` |
| `compiler_render_prompt` | `def compiler_render_prompt(ctx: typer.Context, work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:783` |
| `compiler_ingest_prose` | `def compiler_ingest_prose(ctx: typer.Context, file: str = typer.Argument(...), work_item: str = typer.Option(..., '--work-item')) -> None` | `src/paperproof/cli/app.py:797` |
| `audit_run` | `def audit_run(ctx: typer.Context, draft: str = typer.Option(..., '--draft')) -> None` | `src/paperproof/cli/app.py:814` |
| `trace_cmd` | `def trace_cmd(ctx: typer.Context, node: str = typer.Option(..., '--node')) -> None` | `src/paperproof/cli/app.py:831` |
| `verify_cmd` | `def verify_cmd(ctx: typer.Context) -> None` | `src/paperproof/cli/app.py:838` |
| `main` | `def main() -> None` | `src/paperproof/cli/app.py:843` |
| `load` | `def load(name: str) -> str` | `src/paperproof/prompts/__init__.py:15` |
| `render_docs_prompt` | `def render_docs_prompt(paths: Paths, work_item_id: str) -> dict[str, Any]` | `src/paperproof/prompts/render.py:211` |
| `render_proof_prompt` | `def render_proof_prompt(paths: Paths, work_item_id: str) -> dict[str, Any]` | `src/paperproof/prompts/render.py:226` |
| `render_compile_prompt` | `def render_compile_prompt(paths: Paths, work_item_id: str) -> dict[str, Any]` | `src/paperproof/prompts/render.py:256` |
| **— Derived DB (DuckDB/semantic) & WebUI —** | | |
| `rebuild` | `rebuild(paths: Paths) -> dict[str, Any]` | `src/paperproof/db/indexer.py:136` |
| `check` | `check(paths: Paths) -> dict[str, Any]` | `src/paperproof/db/indexer.py:219` |
| `IndexReader` | `class IndexReader: __init__(self, db_path: str \| Path) -> None; close(); __enter__()->IndexReader; __exit__(*exc); current(table)->list[dict]; history(table)->list[dict]; history_for_id(table, rid)->list[dict]` | `src/paperproof/db/indexer.py:261` |
| `deps_available` | `deps_available() -> bool` | `src/paperproof/db/semantic.py:61` |
| `model_pin` | `model_pin() -> dict[str, str]` | `src/paperproof/db/semantic.py:75` |
| `ensure_model` | `ensure_model(paths: Paths) -> None` | `src/paperproof/db/semantic.py:129` |
| `model_present` | `model_present(paths: Paths) -> bool` | `src/paperproof/db/semantic.py:158` |
| `embed_texts` | `embed_texts(paths: Paths, texts: list[str], prefix: str) # returns np.ndarray (n,384) float32` | `src/paperproof/db/semantic.py:221` |
| `embed_claim` | `embed_claim(paths: Paths, claim: str) # returns np.float32[384]` | `src/paperproof/db/semantic.py:246` |
| `normalize_eu_text` | `normalize_eu_text(eu: dict[str, Any]) -> str` | `src/paperproof/db/semantic.py:251` |
| `normalize_claim_text` | `normalize_claim_text(claim: str) -> str` | `src/paperproof/db/semantic.py:257` |
| `load_vectors` | `load_vectors(paths: Paths) # returns dict[str, np.float32[384]]` | `src/paperproof/db/semantic.py:283` |
| `rebuild` | `rebuild(paths: Paths) -> dict[str, Any]` | `src/paperproof/db/semantic.py:300` |
| `check` | `check(paths: Paths) -> dict[str, Any]` | `src/paperproof/db/semantic.py:338` |
| `advisory_leads` | `advisory_leads(paths: Paths, need: str, hints: list[str] \| None, k: int = 3) -> list[dict[str, Any]]` | `src/paperproof/db/semantic.py:388` |
| `create_app` | `create_app(root: str \| Path, project: str, auto_rebuild: bool = False) -> FastAPI` | `src/paperproof/ui/app.py:48` |
| `serve` | `serve(paths: Paths, port: int = 8420, auto_rebuild: bool = False) -> dict[str, Any]` | `src/paperproof/ui/app.py:171` |
| `overview` | `overview(reader, paths: Paths) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:37` |
| `graph` | `graph(reader, lane: str \| None = None, layer: int \| None = None, state: str \| None = None) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:234` |
| `record` | `record(reader, rid: str) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:259` |
| `queue` | `queue(reader, queue_name: str \| None = None, status: str \| None = None) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:275` |
| `events` | `events(reader, after: str \| None = None, limit: int \| None = None) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:292` |
| `evidence` | `evidence(reader, q: str \| None = None) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:306` |
| `coverage` | `coverage(reader, paths: Paths, node: Optional[str] = None) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:333` |
| `compiler` | `compiler(reader, paths: Paths) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:344` |
| `trace` | `trace(reader, paths: Paths, node_id: str) -> dict[str, Any]` | `src/paperproof/ui/readmodel.py:368` |

## Intentionally internal (excluded from coverage)

- `shared` — extractor false positive: a docstring line in `src/paperproof/committer/__init__.py:4` happens to start with the words "function shared"; there is no such symbol in the code.
