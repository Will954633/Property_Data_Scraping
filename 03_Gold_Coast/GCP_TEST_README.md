# Google Cloud Test Deployment - 5 Addresses

This guide walks you through testing the property scraper on Google Cloud with 5 sample addresses.

## Files Created

1. **test_addresses_5.json** - 5 test addresses extracted from MongoDB
2. **test_scraper_gcs.py** - Standalone scraper for GCP (reads from JSON file)
3. **gcp_startup_script.sh** - VM initialization script
4. **deploy_test_gcp.sh** - Main deployment script

## Test Addresses

The following 5 addresses will be scraped:

1. 414 MARINE PARADE BIGGERA WATERS QLD 4215
2. 8 MATINA STREET BIGGERA WATERS QLD 4216
3. 77 BRISBANE ROAD BIGGERA WATERS QLD 4216
4. 11 MATINA STREET BIGGERA WATERS QLD 4216
5. U 12/414 MARINE PARADE BIGGERA WATERS QLD 4215

## Prerequisites

The gcloud SDK is currently installing. Once complete, you need to:

1. **Initialize gcloud** (if not done):
   ```bash
   exec -l $SHELL  # Reload shell to get gcloud in PATH
   gcloud init
   ```

2. **Authenticate**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set project**:
   ```bash
   gcloud config set project property-data-scraping-477306
   ```

## Deployment Steps

### Step 1: Deploy Test VM

```bash
cd 03_Gold_Coast
./deploy_test_gcp.sh
```

This will:
- Enable required GCP APIs
- Create GCS bucket for test data
- Launch a VM instance
- Install Chrome and dependencies on the VM
- Run the scraper on 5 addresses
- Save results to GCS
- Automatically shutdown the VM

**Expected time:** ~3-5 minutes total

### Step 2: Monitor Progress

Watch the VM startup and execution:

```bash
# Stream logs (updates every few seconds)
gcloud compute instances get-serial-port-output property-scraper-test --zone=us-central1-a

# Or check instance status
gcloud compute instances describe property-scraper-test --zone=us-central1-a
```

### Step 3: Check Results in GCS

Once the scraper completes (VM status becomes TERMINATED):

```bash
# List all files in GCS
gsutil ls -r gs://property-scraper-test-data-477306/test_data/

# Should show 5 JSON files like:
# gs://property-scraper-test-data-477306/test_data/biggera_waters/1853283.json
# gs://property-scraper-test-data-477306/test_data/biggera_waters/451212.json
# etc.
```

### Step 4: Download Results

```bash
# Download to local directory
cd 03_Gold_Coast
mkdir -p test_results
gsutil -m cp -r gs://property-scraper-test-data-477306/test_data/ ./test_results/

# Verify download
ls -la test_results/test_data/biggera_waters/
```

### Step 5: Inspect Data

```bash
# View a sample result
cat test_results/test_data/biggera_waters/1853283.json | python3 -m json.tool
```

**Expected data fields:**
- `url` - Domain.com.au property URL
- `address` - Full property address
- `scraped_at` - Timestamp
- `features` - bedrooms, bathrooms, car_spaces, land_size, property_type
- `valuation` - low, mid, high prices, accuracy, date
- `rental_estimate` - weekly_rent, yield
- `property_timeline` - Historical listings/sales
- `images` - Array of property images with URLs
- `address_pid` - Unique address identifier
- `suburb` - Locality name
- `collection` - MongoDB collection name
- `doc_id` - MongoDB document ID

## Verification Checklist

After downloading results, verify:

- [ ] All 5 JSON files present
- [ ] Each file contains valid JSON
- [ ] `features` section has bedrooms, bathrooms, property_type
- [ ] `valuation` section has price estimates (low, mid, high)
- [ ] `rental_estimate` has weekly rent estimate
- [ ] `images` array contains property photos
- [ ] `property_timeline` has historical listing data
- [ ] No critical errors in the data

## Cleanup

After verifying results:

```bash
# Delete test VM (if not auto-shutdown)
gcloud compute instances delete property-scraper-test --zone=us-central1-a --quiet

# Optional: Delete test data from GCS
gsutil -m rm -r gs://property-scraper-test-data-477306/test_data/

# Optional: Delete entire test bucket
gsutil rb gs://property-scraper-test-data-477306
```

## Cost Estimate

- VM (e2-medium): ~$0.03 for 3-5 minutes
- GCS storage: ~$0.0001 for 5 JSON files
- Network: ~$0.001

**Total: ~$0.03** (3 cents)

## Troubleshooting

### Issue: gcloud command not found

```bash
# Reload shell
exec -l $SHELL

# Or add to PATH manually
source ~/google-cloud-sdk/path.bash.inc
```

### Issue: Authentication error

```bash
gcloud auth login
gcloud auth application-default login
```

### Issue: No files in GCS

1. Check VM logs for errors:
   ```bash
   gcloud compute instances get-serial-port-output property-scraper-test --zone=us-central1-a | tail -100
   ```

2. Check if VM is still running:
   ```bash
   gcloud compute instances list
   ```

3. SSH into VM to debug (if still running):
   ```bash
   gcloud compute ssh property-scraper-test --zone=us-central1-a
   cd /opt/scraper
   ls -la
   cat test_addresses_5.json
   ```

### Issue: ChromeDriver errors

The startup script installs a specific ChromeDriver version (131.0.6778.204). If there are compatibility issues, the script will fail. Check the VM logs for Chrome-related errors.

## Next Steps

After successful test:

1. **Review the data** - Ensure all required fields are populated
2. **Scale up** - Modify deploy script to create multiple workers
3. **Full deployment** - Use the full MongoDB-connected scraper for 300k+ addresses

## Architecture Notes

**Test Setup:**
- Single VM
- Reads from JSON file (no MongoDB connection needed)
- Saves directly to GCS
- Auto-shutdown after completion

**Production Setup (for 300k addresses):**
- 200 VMs (workers)
- Each reads from MongoDB
- Partitioned address ranges
- All save to GCS
- Parallel execution (~15-20 hours)

## Support

If you encounter issues:
1. Check VM serial port logs
2. Verify GCS bucket access
3. Ensure proper authentication
4. Review error messages in output

The test setup is designed to be quick and low-cost to validate the scraping logic before scaling to full production deployment.
