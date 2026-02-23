// Extract __NEXT_DATA__ and save it
const nextData = document.getElementById('__NEXT_DATA__');
if (nextData) {
    const data = JSON.parse(nextData.textContent);
    const apollo = data.props.pageProps.__APOLLO_STATE__;
    
    // Convert to JSON string
    const output = JSON.stringify(apollo, null, 2);
    
    // Create a download
    const blob = new Blob([output], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'apollo_state.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('Apollo state downloaded');
    console.log('Total keys:', Object.keys(apollo).length);
} else {
    console.log('ERROR: __NEXT_DATA__ not found');
}
