# YouTube Pipeline Optimization Plan

## Current vs. Optimized Comparison

### Current Pipeline (SDXL-Turbo + SVD)
**Speed:** ~3 min per scene
**Steps:**
1. SDXL-Turbo generates image (512x512)
2. SVD animates to video (25 steps)

**Pros:**
- Working reliably ✅
- Already generated 4 videos today
- Videos getting views (93 in 2 hours)

**Cons:**
- Sometimes robotic motion
- Occasional artifacts

### Optimized Pipeline (SDXL + WAN2.2 5B + LightX2V)
**Speed:** ~2 min per scene (33% faster!)
**Steps:**
1. SDXL generates image (512x512) - same
2. WAN2.2 5B + LightX2V LoRA animates (8 steps vs 25!)

**Improvements:**
- ✅ **Faster:** 8 steps vs 25 (62% reduction)
- ✅ **Better motion:** WAN2.2 has more natural movement
- ✅ **24fps output:** Smoother than current
- ✅ **Same VRAM:** Both fit in 16GB

## Key Optimization: LightX2V LoRA

**What it does:** Distillation model that achieves same quality in fewer steps
- Normal WAN2.2: 25-30 steps
- With LightX2V: 8-10 steps
- **Result:** 3x faster generation!

## Implementation Plan

### Phase 1: Test Single Scene (30 min)
1. ✅ Downloaded LightX2V LoRA
2. Create workflow: SDXL → WAN2.2 + LoRA
3. Generate 1 test scene
4. Compare with current SVD output
5. **Decision point:** Quality worth the switch?

### Phase 2: Integration (1-2 hours)
If test is successful:
1. Modify `batch_generate_upload_series.py`
2. Add `--backend=wan22` option
3. Keep SVD as fallback
4. Test with full 4-video generation

### Phase 3: Production (immediate)
- Make WAN2.2 the default
- Update cron jobs
- Monitor performance

## Estimated Impact

**Current:** 4 videos × 6 scenes × 3 min = 72 minutes
**Optimized:** 4 videos × 6 scenes × 2 min = 48 minutes

**Time saved:** 24 minutes per day (33% faster!)

**Quality:** Expected to be better (more natural motion, 24fps)

## Next Step

Let me create the complete optimized workflow and test with 1 scene. If you approve the quality, we'll integrate it into the pipeline.

Want me to proceed with the test?
