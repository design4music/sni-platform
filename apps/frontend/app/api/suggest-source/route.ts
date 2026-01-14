import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { outlet, website, country, comment } = body;

    // Validate required fields
    if (!outlet || !website || !country) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Recipient email
    const recipientEmail = 'max.micheliov@gmail.com';

    // Email content
    const emailBody = `
New Source Suggestion from WorldBrief

Outlet Name: ${outlet}
Website: ${website}
Country: ${country}
Comment: ${comment || 'None'}

Submitted at: ${new Date().toISOString()}
    `.trim();

    // TODO: Send email using your preferred service
    // Option 1: Use Resend (simple, free tier)
    // Option 2: Use nodemailer with SMTP
    // Option 3: Use SendGrid

    // For now, log to console (you'll see this in the daemon/server output)
    console.log('\n=== NEW SOURCE SUGGESTION ===');
    console.log(emailBody);
    console.log('============================\n');

    // Placeholder response - replace with actual email sending
    // When you set up email service, replace the console.log with actual sending

    /* Example with Resend (recommended):

    import { Resend } from 'resend';
    const resend = new Resend(process.env.RESEND_API_KEY);

    await resend.emails.send({
      from: 'WorldBrief <noreply@yourdomain.com>',
      to: recipientEmail,
      subject: `New Source Suggestion: ${outlet}`,
      text: emailBody,
    });
    */

    return NextResponse.json({
      success: true,
      message: 'Suggestion submitted successfully'
    });

  } catch (error) {
    console.error('Error processing source suggestion:', error);
    return NextResponse.json(
      { error: 'Failed to submit suggestion' },
      { status: 500 }
    );
  }
}
