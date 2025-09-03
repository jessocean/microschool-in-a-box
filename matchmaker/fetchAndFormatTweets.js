const fs = require('fs')

function formatTweets(archiveData, handle, startDate, endDate) {
  const tweets = archiveData.tweets.map(x => ({date: new Date(x.tweet.created_at), text: x.tweet.full_text}))
  const filtered = tweets.filter(x => {
    const date = x.date
    return date >= new Date(startDate) && date < new Date(endDate)
  })
  const formatted = filtered.map(x => x.date.toISOString().replace(/\.000Z/, '').replace(/(\d)T(\d)/, '$1 at $2') + ': ' + x.text).join('\n\n')
 
  const outputPath = `${handle}_${startDate}_to_${endDate}.txt`
  fs.writeFileSync(outputPath, formatted)
}

async function fetchAndFormatTweets(handle, startDate, endDate) {
  const url = `https://fabxmporizzqflnftavs.supabase.co/storage/v1/object/public/archives/${handle}/archive.json`
 
  try {
    const response = await fetch(url)
    if (!response.ok) {
      console.error(`Archive not found for handle: ${handle}`)
      return
    }
   
    const archiveData = await response.json()
    formatTweets(archiveData, handle, startDate, endDate)
  } catch (error) {
    console.error(`Error fetching archive for ${handle}:`, error.message)
  }
}

if (require.main === module) {
  const [,, handle, startDate, endDate] = process.argv
  if (!handle || !startDate || !endDate) {
    console.error('Usage: node fetchAndFormatTweets.js <handle> <start-date> <end-date>')
    process.exit(1)
  }
  fetchAndFormatTweets(handle, startDate, endDate)
}