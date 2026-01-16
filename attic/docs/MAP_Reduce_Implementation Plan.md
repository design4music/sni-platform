  📋 Implementation Plan

  New Files to Create:

  apps/generate/
  ├── mapreduce_processor.py       # Main MAP/REDUCE orchestrator
  ├── map_classifier.py            # Pass-1a MAP: title classification
  ├── reduce_assembler.py          # Pass-1c REDUCE: EF title/summary generation
  ├── mapreduce_models.py          # Pydantic models for MAP/REDUCE
  └── mapreduce_prompts.py         # Minimal prompts for MAP/REDUCE

  Files to Modify (minimally):

  core/config.py                   # Add MAP/REDUCE config section
  apps/generate/database.py        # Add EF upsert method (if not exists)
  run_pipeline.py                  # Add --mapreduce flag option

  🏗️ Detailed Implementation

  1. New Configuration (core/config.py)

  # Add to existing SNIConfig class
  class SNIConfig(BaseSettings):
      # ... existing config ...

      # MAP/REDUCE Configuration
      mapreduce_enabled: bool = Field(default=False, env="MAPREDUCE_ENABLED")
      map_batch_size: int = Field(default=150, env="MAP_BATCH_SIZE")
      map_concurrency: int = Field(default=4, env="MAP_CONCURRENCY")
      map_timeout_seconds: int = Field(default=90, env="MAP_TIMEOUT_SECONDS")
      reduce_concurrency: int = Field(default=8, env="REDUCE_CONCURRENCY")
      reduce_timeout_seconds: int = Field(default=45, env="REDUCE_TIMEOUT_SECONDS")
      reduce_max_titles: int = Field(default=12, env="REDUCE_MAX_TITLES")

  2. New Models (apps/generate/mapreduce_models.py)

  from pydantic import BaseModel
  from typing import List, Dict, Any

  class TitleClassification(BaseModel):
      id: str
      primary_theater: str
      event_type: str

  class MapRequest(BaseModel):
      titles: List[Dict[str, str]]  # [{"id": "...", "title": "..."}]

  class MapResponse(BaseModel):
      classifications: List[TitleClassification]

  class EFGroup(BaseModel):
      primary_theater: str
      event_type: str
      title_ids: List[str]
      titles: List[Dict[str, str]]
      temporal_scope_start: datetime
      temporal_scope_end: datetime

  class ReduceRequest(BaseModel):
      ef_context: Dict[str, str]  # {"primary_theater": "...", "event_type": "..."}
      titles: List[Dict[str, str]]  # Up to 12 titles

  class ReduceResponse(BaseModel):
      ef_title: str
      ef_summary: str

  3. MAP Classifier (apps/generate/map_classifier.py)

  class MapClassifier:
      def __init__(self, config: SNIConfig):
          self.config = config
          self.llm_client = get_gen1_llm_client()

      async def classify_titles_batch(self, titles: List[Dict[str, str]]) -> List[TitleClassification]:
          """Classify a batch of titles into theater + event_type"""

      async def process_titles_parallel(self, all_titles: List[Dict[str, str]]) -> List[TitleClassification]:
          """Process all titles with parallel MAP calls"""

  4. REDUCE Assembler (apps/generate/reduce_assembler.py)

  class ReduceAssembler:
      def __init__(self, config: SNIConfig):
          self.config = config
          self.llm_client = get_gen1_llm_client()

      async def generate_ef_content(self, ef_group: EFGroup) -> ReduceResponse:
          """Generate EF title/summary for a group"""

      async def process_groups_parallel(self, ef_groups: List[EFGroup]) -> List[EventFamily]:
          """Process all EF groups with parallel REDUCE calls"""

  5. Main Orchestrator (apps/generate/mapreduce_processor.py)

  class MapReduceProcessor:
      """
      MAP/REDUCE Event Family processor

      Alternative to MultiPassProcessor with parallel processing
      """

      def __init__(self):
          self.config = get_config()
          self.db = get_gen1_database()
          self.mapper = MapClassifier(self.config)
          self.reducer = ReduceAssembler(self.config)

      async def run_pass1_mapreduce(self, max_titles: Optional[int] = None) -> ProcessingResult:
          """
          MAP/REDUCE Pass 1: Parallel title classification and EF assembly

          1. MAP: Classify titles -> (theater, event_type) in parallel
          2. GROUP: Group by (theater, event_type)
          3. REDUCE: Generate EF content per group in parallel
          4. UPSERT: Merge with existing EFs by ef_key
          """

      def _group_classifications(self, classifications: List[TitleClassification],
                               titles: List[Dict]) -> List[EFGroup]:
          """Group classifications by (theater, event_type)"""

      async def _upsert_event_families(self, event_families: List[EventFamily]) -> Dict[str, Any]:
          """Upsert EFs by ef_key with existing database logic"""

  # CLI interface
  if __name__ == "__main__":
      import typer
      app = typer.Typer()

      @app.command()
      async def run_mapreduce(max_titles: int = 1000):
          processor = MapReduceProcessor()
          result = await processor.run_pass1_mapreduce(max_titles)
          print(f"MAP/REDUCE Results: {result.summary}")

  6. Minimal Prompts (apps/generate/mapreduce_prompts.py)

  CLASSIFICATION_SYSTEM_PROMPT = """Classify each title into exactly one primary_theater and one event_type from the enums
  provided. Output one compact JSON object per input title (JSON Lines). Use only given IDs. No external facts."""

  CLASSIFICATION_USER_TEMPLATE = """EVENT_TYPES = {event_types}
  THEATERS = {theaters}
  Return JSON Lines only, one per title:
  {{"id":"...", "primary_theater":"THEATER_ID", "event_type":"EVENT_TYPE"}}

  INPUT (id | title):
  {titles}"""

  EF_GENERATION_SYSTEM_PROMPT = """Given one provisional EF (primary_theater + event_type) and up to 12 titles (id+title),
  produce a concise EF title (≤120 chars) and EF summary (≤280 chars) describing the recurring pattern (not a single incident).
  No outside facts."""

  EF_GENERATION_USER_TEMPLATE = """EF CONTEXT: primary_theater={primary_theater}, event_type={event_type}
  TITLES (id | title):
  {titles}
  Return JSON only: {{"ef_title":"...", "ef_summary":"..."}}"""

  7. Pipeline Integration (run_pipeline.py)

  # Add new command option
  @app.command()
  async def phase3_mapreduce(
      max_titles: int = typer.Option(1000, help="Maximum titles to process"),
      dry_run: bool = typer.Option(False, help="Dry run mode")
  ):
      """Phase 3: MAP/REDUCE Event Family Generation (Alternative Implementation)"""

      async def run_mapreduce():
          config = get_config()
          if not config.mapreduce_enabled:
              print("MAP/REDUCE processing disabled in config")
              return

          from apps.generate.mapreduce_processor import MapReduceProcessor
          processor = MapReduceProcessor()
          result = await processor.run_pass1_mapreduce(max_titles)
          print(f"MAP/REDUCE result: {result}")

      asyncio.run(run_mapreduce())

  # Modify existing phase3 to support both approaches
  @app.command()
  async def phase3(
      max_titles: int = typer.Option(1000, help="Maximum titles to process"),
      algorithm: str = typer.Option("multipass", help="Algorithm: 'multipass' or 'mapreduce'"),
  ):
      """Phase 3: Event Family Generation (Choose Algorithm)"""

      if algorithm == "mapreduce":
          await phase3_mapreduce(max_titles)
      else:
          await phase3_multipass(max_titles)  # Existing implementation

  🧪 Testing Strategy

  A/B Testing Setup:

  # Test current system
  python run_pipeline.py phase3 --max-titles=500 --algorithm=multipass

  # Test new MAP/REDUCE system
  python run_pipeline.py phase3 --max-titles=500 --algorithm=mapreduce

  # Direct comparison
  python -m apps.generate.mapreduce_processor run-mapreduce 500

  Environment Variables:

  # .env additions
  MAPREDUCE_ENABLED=false  # Safe default
  MAP_BATCH_SIZE=150
  MAP_CONCURRENCY=4
  MAP_TIMEOUT_SECONDS=90
  REDUCE_CONCURRENCY=8
  REDUCE_TIMEOUT_SECONDS=45
  REDUCE_MAX_TITLES=12

  ✅ Migration Path

  1. Phase 1: Create new files, test in isolation
  2. Phase 2: A/B test both systems on same dataset
  3. Phase 3: Performance comparison and tuning
  4. Phase 4: Switch default if MAP/REDUCE proves superior
  5. Phase 5: Eventually deprecate multipass_processor.py

  🔒 Safety Guarantees

  - ✅ Zero impact on existing system
  - ✅ Separate entry points for testing
  - ✅ Shared database layer (same EF schema)
  - ✅ Same configuration infrastructure
  - ✅ Easy rollback if issues arise

  This approach gives us a clean, safe way to validate the MAP/REDUCE concept while maintaining the current working system as our
   fallback.