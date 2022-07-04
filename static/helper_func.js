function CopyToClipboard(id) {
    let textToCopy = document.getElementById(id).innerText;
    if(navigator.clipboard) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            alert('Copied to clipboard')
        })
    } else {
        console.log('Browser Not compatible')
    }
}
