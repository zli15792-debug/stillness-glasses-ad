// Usage: text <out.png> <y_center_fraction> <fontName> <size> <kern> <text> [<fontName2> <size2> <kern2> <text2> <gap>]
import Foundation
import CoreGraphics
import CoreText
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
let W = 1920, H = 1080
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0,
                    space: CGColorSpace(name: CGColorSpace.sRGB)!,
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.clear(CGRect(x: 0, y: 0, width: W, height: H))

func line(_ font: String, _ size: Double, _ kern: Double, _ s: String) -> CTLine {
    let f = CTFontCreateWithName(font as CFString, size, nil)
    let attrs: [NSAttributedString.Key: Any] = [
        NSAttributedString.Key(kCTFontAttributeName as String): f,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(red: 0.96, green: 0.93, blue: 0.86, alpha: 1),
        NSAttributedString.Key(kCTKernAttributeName as String): kern,
    ]
    return CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: attrs))
}

func draw(_ l: CTLine, centerY: Double) {
    var asc: CGFloat = 0, desc: CGFloat = 0, lead: CGFloat = 0
    let w = CTLineGetTypographicBounds(l, &asc, &desc, &lead)
    ctx.textPosition = CGPoint(x: (Double(W) - w) / 2, y: centerY - Double(asc - desc) / 2)
    ctx.setShadow(offset: .zero, blur: 18, color: CGColor(red: 0, green: 0, blue: 0, alpha: 0.55))
    CTLineDraw(l, ctx)
}

let yc = Double(H) * (1 - Double(a[2])!)
let l1 = line(a[3], Double(a[4])!, Double(a[5])!, a[6])
if a.count > 11 {
    let l2 = line(a[7], Double(a[8])!, Double(a[9])!, a[10])
    let gap = Double(a[11])!
    draw(l1, centerY: yc + gap / 2)
    draw(l2, centerY: yc - gap / 2)
} else {
    draw(l1, centerY: yc)
}

let img = ctx.makeImage()!
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[1]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, img, nil)
CGImageDestinationFinalize(dest)
