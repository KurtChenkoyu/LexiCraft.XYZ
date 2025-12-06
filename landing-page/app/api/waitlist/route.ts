import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

export async function POST(request: NextRequest) {
  try {
    const { email, numKids } = await request.json()

    // Validate input
    if (!email || !numKids) {
      return NextResponse.json(
        { error: 'Email and number of kids are required' },
        { status: 400 }
      )
    }

    // Determine which email service to use
    const emailService = process.env.NEXT_PUBLIC_EMAIL_SERVICE || 'convertkit'
    
    if (emailService === 'convertkit') {
      return await handleConvertKit(email, numKids)
    } else if (emailService === 'mailchimp') {
      return await handleMailchimp(email, numKids)
    } else {
      // Fallback: Just log the submission (for testing)
      console.log('Waitlist submission:', { email, numKids })
      return NextResponse.json({ success: true, message: 'Waitlist signup recorded' })
    }
  } catch (error) {
    console.error('Waitlist API error:', error)
    return NextResponse.json(
      { error: 'Failed to process waitlist signup' },
      { status: 500 }
    )
  }
}

async function handleConvertKit(email: string, numKids: number) {
  const apiKey = process.env.CONVERTKIT_API_KEY
  const formId = process.env.CONVERTKIT_FORM_ID

  if (!apiKey || !formId) {
    console.error('ConvertKit credentials not configured')
    return NextResponse.json(
      { error: 'Email service not configured' },
      { status: 500 }
    )
  }

  try {
    const response = await axios.post(
      `https://api.convertkit.com/v3/forms/${formId}/subscribe`,
      {
        api_key: apiKey,
        email,
        fields: {
          num_kids: numKids.toString(),
        },
      }
    )

    return NextResponse.json({
      success: true,
      message: 'Successfully joined waitlist',
      data: response.data,
    })
  } catch (error: any) {
    console.error('ConvertKit error:', error.response?.data || error.message)
    return NextResponse.json(
      { error: 'Failed to subscribe to waitlist' },
      { status: 500 }
    )
  }
}

async function handleMailchimp(email: string, numKids: number) {
  const apiKey = process.env.MAILCHIMP_API_KEY
  const listId = process.env.MAILCHIMP_LIST_ID
  const serverPrefix = process.env.MAILCHIMP_SERVER_PREFIX || 'us1'

  if (!apiKey || !listId) {
    console.error('Mailchimp credentials not configured')
    return NextResponse.json(
      { error: 'Email service not configured' },
      { status: 500 }
    )
  }

  try {
    const response = await axios.post(
      `https://${serverPrefix}.api.mailchimp.com/3.0/lists/${listId}/members`,
      {
        email_address: email,
        status: 'subscribed',
        merge_fields: {
          NUMKIDS: numKids.toString(),
        },
      },
      {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      }
    )

    return NextResponse.json({
      success: true,
      message: 'Successfully joined waitlist',
      data: response.data,
    })
  } catch (error: any) {
    console.error('Mailchimp error:', error.response?.data || error.message)
    
    // Handle "already subscribed" case
    if (error.response?.status === 400 && error.response?.data?.title === 'Member Exists') {
      return NextResponse.json({
        success: true,
        message: 'You are already on the waitlist',
      })
    }

    return NextResponse.json(
      { error: 'Failed to subscribe to waitlist' },
      { status: 500 }
    )
  }
}

